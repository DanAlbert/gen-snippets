import gerrit
import json
import sys

from datetime import date, timedelta


def get_last_week_range():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday - timedelta(weeks=1), monday - timedelta(days=1)


def change_url(change):
    """Generates a URL for a given change."""
    return '{base_url}/#/c/{number}'.format(
        base_url=gerrit.base_url,
        number=change['_number'])


def pretty_project_name(project_name):
    def strip_leading(component, path):
        if path.startswith(component):
            return path.partition('/')[2]
        return path

    project_name = strip_leading('platform/', project_name)
    project_name = strip_leading('external/', project_name)
    return project_name


def make_snippets(projects):
    lines = []
    for project, changes in projects.items():
        lines.append('* {}:'.format(pretty_project_name(project)))
        for change in changes:
            subject = change['subject']
            if subject.endswith('.'):
                subject = subject[:-1]
            url = change_url(change)
            lines.append('    * {}: {}'.format(subject, url))
    return '\n'.join(lines)


def main():
    try:
        import userconfig
    except ImportError:
        sys.exit('userconfig.py not found')

    user = userconfig.username
    monday, sunday = get_last_week_range()

    query = 'owner:{}+after:{}+before:{}'.format(user, monday, sunday)
    response = gerrit.call('/changes/?q={}'.format(query))
    changes = json.loads(response)

    project_names = {c['project'] for c in changes}
    projects = {pn: [] for pn in project_names}
    for change in changes:
        projects[change['project']].append(change)

    print make_snippets(projects)


if __name__ == '__main__':
    main()
