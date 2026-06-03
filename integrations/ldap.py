"""
Project scaffolding for future LDAP / Active Directory synchronization.

The functions in this module intentionally do not connect to real directory
services yet. They document the expected data contract so the integration can
be implemented later without changing the public API.
"""


def sync_from_ldap():
    """
    Synchronize organization data from LDAP.

    Expected incoming fields per person entry:
    - username
    - email
    - first_name
    - last_name
    - department
    - position
    - role

    Expected organizational fields:
    - department name
    - position name

    TODO:
    - connect to LDAP server;
    - map LDAP attributes to local Department / Position / Profile objects;
    - apply incremental updates;
    - record IntegrationSyncLog entries.
    """
    raise NotImplementedError('LDAP synchronization is not implemented yet.')


def sync_from_active_directory():
    """
    Synchronize organization data from Active Directory.

    Expected incoming fields per person entry:
    - sAMAccountName or userPrincipalName as username
    - mail as email
    - givenName as first_name
    - sn as last_name
    - department
    - title or jobTitle as position
    - a role mapping rule for employee / security_officer / admin

    Expected organizational fields:
    - department
    - title/job title

    TODO:
    - connect to AD;
    - map directory attributes to local models;
    - support delta sync;
    - write detailed sync logs.
    """
    raise NotImplementedError('Active Directory synchronization is not implemented yet.')
