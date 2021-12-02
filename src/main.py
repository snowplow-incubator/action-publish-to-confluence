import os
import json
import re
from pymojihash import hash_to_emoji


workspace = os.environ.get('GITHUB_WORKSPACE')
if not workspace:
    raise Exception('No workspace is set')

envs = {}
for key in ['repository', 'branch', 'confluence_url', 'confluence_username', 'confluence_token', 'confluence_space']:
    value = os.environ.get(f'INPUT_{key.upper()}')
    if not value:
        raise Exception(f'Missing value for {key}')
    envs[key] = value

def get_markdown_files_and_directories(folder):
    directories = []
    markdown_files = []
    for item in os.listdir(folder):
        if item[0] == '.': continue
        file_path = f'{folder}/{item}'

        if os.path.isdir(file_path):
            directories.append(file_path)
        elif item.endswith('.md'):
            markdown_files.append(file_path)

    return markdown_files, directories

def get_title(file_path, parent_titles):
    with open(file_path) as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('<!--'): continue
                if line.startswith('#'): line = line[1:]
                return append_hash_to_title(line.strip(), parent_titles)

    return folder_to_title(file_path, parent_titles)

def get_folder_structure(folder):
    markdown_files, directories = get_markdown_files_and_directories(folder)

    children = []
    for directory in directories:
        for directory_structure in get_folder_structure(directory):
            if directory_structure is not None:
                children.append(directory_structure)

    if len(markdown_files) == 0:
        return children

    main_files = [f for f in markdown_files if f.lower().endswith('index.md') or f.lower().endswith('readme.md')]
    markdown_files = [f for f in markdown_files if f not in main_files]

    structure = {
        'folder': folder,
        'siblings': markdown_files,
        'children': children
    }
    if len(main_files) > 0:
        main_file = main_files[0]
        structure['file'] = main_file

    return [structure]

def push_file_to_confluence(file_path, title, parent_title):
    with open(file_path, 'r') as f:
        content = f.read()

    push_content_to_confluence(
        content=content,
        folder=os.path.dirname(file_path),
        title=title,
        parent_title=parent_title,
        file_path=file_path
    )

def find_images_in_markdown(content):
    regex = r"!\[[^\]]*\]\((?P<filename>.*?)(?=\"|\))(?P<optionalpart>\".*\")?\)"
    matches = re.finditer(regex, content)

    images = []
    for _, match in enumerate(matches, start=1):
        groups = match.groupdict()
        images.append(groups['filename'].strip())
    return images

def push_content_to_confluence(content, folder, title, parent_title, file_path=None):
    space = envs['confluence_space']
    repository = envs['repository']
    branch = envs['branch']

    headers = []
    if parent_title is not None:
        headers.append(f'<!-- Parent: {parent_title} -->')
    images = find_images_in_markdown(content)
    for image in images:
        headers.append(f'<!-- Attachment: {image} -->')
    headers.append(f'<!-- Space: {space} -->')
    headers.append(f'<!-- Title: {title} -->')

    parts = [
        '\n'.join(headers),
        content
    ]
    if file_path is not None:
        parts.append('')
        parts.append(f'[Open on Github.](https://github.com/{repository}/blob/{branch}/{repository_file_path(file_path)})')
    content = '\n'.join(parts)

    tmp_file_path = f'{folder}/_mark_tmp.md'
    with open(tmp_file_path, 'w') as f:
        f.write(content)

    mark_executable = os.getenv('MARK_EXECUTABLE', default='mark')
    username = envs['confluence_username']
    password = envs['confluence_token']
    confluence_url = envs['confluence_url']

    os.system(f'cd {folder} && {mark_executable} -u {username} -p {password} -b {confluence_url} -f _mark_tmp.md')

    os.remove(tmp_file_path)

def repository_file_path(file_path):
    if file_path.startswith(workspace): file_path = file_path[len(workspace):]
    if file_path.startswith('/'): file_path = file_path[1:]
    return file_path

def folder_to_title(folder, parent_titles):
    title = folder
    if title.startswith(workspace): title = title[len(workspace):]
    if title.startswith('/'): title = title[1:]
    title = title.replace('/', ' – ')
    return append_hash_to_title(title, parent_titles)

def append_hash_to_title(title, parent_titles):
    if len(parent_titles) == 0: return title
    emoji = hash_to_emoji('-'.join(parent_titles))
    return f'{title} {emoji}'

def process_and_upload_folder_structure(folder_structure, parent_titles):
    print('Publishing', folder_structure['folder'])
    parent_title = parent_titles[-1] if len(parent_titles) > 0 else None

    if 'file' in folder_structure: # there is a main file to use as parent
        file_path = folder_structure['file']
        title = get_title(file_path, parent_titles)
        push_file_to_confluence(file_path=file_path, title=title, parent_title=parent_title)
    else: # there is no file to use as parent, create an empty one
        title = folder_to_title(folder_structure['folder'], parent_titles)
        push_content_to_confluence(
            content='',
            folder=folder_structure['folder'],
            title=title,
            parent_title=parent_title
        )

    for sibling in folder_structure["siblings"]:
        push_file_to_confluence(file_path=sibling, title=get_title(sibling, parent_titles + [title]), parent_title=title)

    for child in folder_structure["children"]:
        process_and_upload_folder_structure(folder_structure=child, parent_titles=parent_titles + [title])

root_structures = get_folder_structure(workspace)
for root_structure in root_structures:
    print(json.dumps(root_structure, indent=4))

    process_and_upload_folder_structure(folder_structure=root_structure, parent_titles=[])
