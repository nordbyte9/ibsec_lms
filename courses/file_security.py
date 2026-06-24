import hashlib
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


DEFAULT_MAX_FILE_SIZE = 20 * 1024 * 1024
CONTROL_CHARACTERS_RE = re.compile(r'[\x00-\x1f\x7f]')

ALLOWED_FILE_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.txt': 'text/plain',
    '.csv': 'text/csv',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
}

ALLOWED_EXTENSIONS = tuple(sorted(ALLOWED_FILE_TYPES))


@dataclass(frozen=True)
class FileInspection:
    original_name: str
    extension: str
    content_type: str
    size: int
    sha256: str


def sanitize_original_filename(filename):
    """Возвращает безопасное исходное имя без каталогов и управляющих символов."""

    normalized = str(filename or '').replace('\\', '/')
    name = Path(normalized).name
    name = CONTROL_CHARACTERS_RE.sub('', name).strip().strip('.')

    if not name:
        raise ValidationError('Не удалось определить имя загружаемого файла.')

    return name[:255]


def _unwrap_file(value):
    return getattr(value, 'file', value)


def _remember_position(file_obj):
    try:
        return file_obj.tell()
    except (AttributeError, OSError):
        return None


def _restore_position(file_obj, position):
    try:
        file_obj.seek(0 if position is None else position)
    except (AttributeError, OSError):
        pass


def _read_head(value, size=8192):
    file_obj = _unwrap_file(value)
    position = _remember_position(file_obj)
    try:
        file_obj.seek(0)
        return file_obj.read(size)
    finally:
        _restore_position(file_obj, position)


def _zip_members(value):
    file_obj = _unwrap_file(value)
    position = _remember_position(file_obj)
    try:
        file_obj.seek(0)
        with zipfile.ZipFile(file_obj) as archive:
            return set(archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return set()
    finally:
        _restore_position(file_obj, position)


def _detect_content_type(value, extension):
    head = _read_head(value)

    if head.startswith(b'%PDF-'):
        detected = 'application/pdf'
    elif head.startswith(b'\x89PNG\r\n\x1a\n'):
        detected = 'image/png'
    elif head.startswith(b'\xff\xd8\xff'):
        detected = 'image/jpeg'
    elif head.startswith(b'PK\x03\x04'):
        members = _zip_members(value)
        if '[Content_Types].xml' not in members:
            raise ValidationError('ZIP-архив не является поддерживаемым офисным документом.')
        if 'word/document.xml' in members:
            detected = ALLOWED_FILE_TYPES['.docx']
        elif 'xl/workbook.xml' in members:
            detected = ALLOWED_FILE_TYPES['.xlsx']
        elif 'ppt/presentation.xml' in members:
            detected = ALLOWED_FILE_TYPES['.pptx']
        else:
            raise ValidationError('Не удалось определить тип офисного документа.')
    elif extension in {'.txt', '.csv'}:
        if b'\x00' in head:
            raise ValidationError('Текстовый файл содержит двоичные данные.')
        try:
            head.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValidationError('Текстовые файлы должны быть сохранены в UTF-8.') from exc
        detected = ALLOWED_FILE_TYPES[extension]
    else:
        raise ValidationError('Фактический тип файла не поддерживается.')

    expected = ALLOWED_FILE_TYPES[extension]
    if detected != expected:
        raise ValidationError(
            'Расширение файла не соответствует его фактическому содержимому.'
        )

    return detected


def _calculate_size(value):
    explicit_size = getattr(value, 'size', None)
    if explicit_size is not None:
        return int(explicit_size)

    file_obj = _unwrap_file(value)
    position = _remember_position(file_obj)
    try:
        file_obj.seek(0, 2)
        return int(file_obj.tell())
    finally:
        _restore_position(file_obj, position)


def _calculate_sha256(value):
    file_obj = _unwrap_file(value)
    position = _remember_position(file_obj)
    digest = hashlib.sha256()

    try:
        file_obj.seek(0)
        while True:
            chunk = file_obj.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        _restore_position(file_obj, position)

    return digest.hexdigest()


def inspect_uploaded_file(value):
    """Проверяет размер, расширение и сигнатуру файла и возвращает метаданные."""

    original_name = sanitize_original_filename(getattr(value, 'name', ''))
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_FILE_TYPES:
        allowed = ', '.join(ALLOWED_EXTENSIONS)
        raise ValidationError(f'Недопустимое расширение файла. Разрешены: {allowed}.')

    size = _calculate_size(value)
    max_size = int(
        getattr(settings, 'PROTECTED_FILE_MAX_SIZE', DEFAULT_MAX_FILE_SIZE)
    )

    if size <= 0:
        raise ValidationError('Нельзя загрузить пустой файл.')

    if size > max_size:
        max_megabytes = max_size / (1024 * 1024)
        raise ValidationError(
            f'Размер файла превышает допустимый предел {max_megabytes:g} МБ.'
        )

    content_type = _detect_content_type(value, extension)

    return FileInspection(
        original_name=original_name,
        extension=extension,
        content_type=content_type,
        size=size,
        sha256=_calculate_sha256(value),
    )


def validate_protected_upload(value):
    inspect_uploaded_file(value)
