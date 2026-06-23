def breadcrumbs(*items):
    trail = []
    for label, url in items:
        trail.append({'label': label, 'url': url})
    return trail
