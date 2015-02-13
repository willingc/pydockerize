#!/usr/bin/env python

import os
import subprocess
import textwrap

import click


DEFAULT_BASE_IMAGES = ['python:2.7-onbuild']


@click.group(chain=True)
@click.version_option()
@click.option('-b', '--base-images',
              default=None,
              help='Base docker images (comma-separated list) - e.g.: '
                   '"python:2.7-onbuild,python:3.4-onbuild". Conflicts with '
                   '--python-versions.')
@click.option('-c', '--cmd',
              help='Command (CMD) to set in image. Conflicts with --procfile')
@click.option('-e', '--entrypoint',
              help='Entry point (ENTRYPOINT) to set in image')
@click.option('-p', '--python-versions',
              default=None,
              help='Python versions (comma-separated list) - e.g.: '
                   '"2.7,3.4". Conflicts with --base-images.')
@click.option('--procfile', type=click.File(),
              help='Procfile to get command from. Conflicts with --cmd.')
@click.option('-t', '--tag',
              help='Repository name (and optionally a tag) to be applied to '
                   'the resulting image in case of success')
@click.option('-r', '--requirement',
              'requirements_file', type=click.Path(exists=True),
              default='requirements.txt')
@click.pass_context
def pydockerize(ctx, requirements_file, tag, cmd, entrypoint, procfile,
                base_images=None, python_versions=None):
    """Create Docker images for Python apps"""

    if base_images is not None and python_versions is not None:
        raise Exception(
            'Cannot specify both --base-images and --python_versions')

    if base_images is not None:
        base_images = base_images.split(',')
    else:
        base_images = DEFAULT_BASE_IMAGES

    if python_versions is not None:
        python_versions = python_versions.split(',')
        base_images = get_base_images_from_python_versions(python_versions)

    if cmd is not None and procfile is not None:
        raise Exception('Cannot specify both --cmd and --procfile')

    if cmd is None and procfile is None and os.path.exists('Procfile'):
        procfile = open('Procfile')

    if procfile:
        cmd = get_cmd_from_procfile(procfile)

    ctx.obj = {
        'base_images': base_images,
        'requirements_file': requirements_file,
        'cmd': cmd,
        'entrypoint': entrypoint,
        'tag': tag,
    }

    click.echo('pydockerize: requirements_file = %r' % requirements_file)
    click.echo('pydockerize: cmd = %r' % cmd)
    click.echo('pydockerize: entrypoint = %r' % entrypoint)

    # if tag:
    #     click.echo('\nShowing Docker images for %s:\n' % tag)
    #     show_docker_images(tag)


@pydockerize.command()
@click.pass_context
def write_dockerfiles(ctx):
    """Write Dockerfile(s)"""

    click.echo('********** write_dockerfiles ********')

    base_images = ctx.obj['base_images']
    requirements_file = ctx.obj['requirements_file']
    cmd = ctx.obj['cmd']
    entrypoint = ctx.obj['entrypoint']

    base_images_and_filenames = []

    for base_image in base_images:
        filename = get_filename_from_base_image(base_image)
        write_dockerfile(base_image, requirements_file,
                         filename, cmd, entrypoint)
        base_images_and_filenames.append((base_image, filename))

    ctx.obj['base_images_and_filenames'] = base_images_and_filenames


def get_base_images_from_python_versions(python_versions):
    return ['python:%s-onbuild' % python_version
            for python_version in python_versions]


def get_cmd_from_procfile(procfile):
    lines = procfile.readlines()
    if len(lines) > 1:
        raise Exception(
            'Procfile with multiple lines not supported')
    return lines[0].split(':')[1].strip()


def write_dockerfile(base_image, requirements_file, filename, cmd, entrypoint):
    click.echo('write_dockerfile: base_image = %r' % base_image)
    click.echo('write_dockerfile: Writing %s' % filename)

    with open(filename, 'w+') as f:
        f.write(textwrap.dedent("""\
            # This Docker image takes care of doing:
            #
            #     pip install -r requirements.txt
            #
            # For more details on this Docker image, see:
            # https://registry.hub.docker.com/_/python/
            FROM {base_image}

            # This is so one can mount a volume from the host to give the
            # container access to the host's current working directory.
            #
            # E.g.:
            #
            #   - `docker run -v $(pwd):/host` from command-line
            #         or
            #   - `volumes: [".:/host"]` in fig.yml
            WORKDIR /host
        """.format(base_image=base_image)))
        if entrypoint:
            f.write("\nENTRYPOINT " + entrypoint)
        if cmd:
            f.write("\nCMD " + cmd)

    return filename


@pydockerize.command(short_help="Run `docker build` with Dockerfile(s) from "
                                "`write_dockerfiles`")
@click.pass_context
def build(ctx):
    """Run `docker build` with Dockerfile(s) from `write_dockerfiles`"""

    tag = ctx.obj['tag']
    base_images = ctx.obj['base_images']

    click.echo('build: tag = %r' % tag)

    for base_image in base_images:
        filename = get_filename_from_base_image(base_image)
        build_one(tag, base_image, filename)


def build_one(tag, base_image, filename):
    cmd = ['docker', 'build']
    if tag:
        if ':' in tag:
            raise Exception("':' in tag not supported yet")
        tag = tag + ':' + get_tag_from_base_image(base_image)
        cmd.append('--tag')
        cmd.append(tag)
    cmd.append('--file')
    cmd.append(filename)
    cmd.append('.')
    click.echo('build_one: Calling subprocess with cmd = %r\n'
               % ' '.join(cmd))
    status = subprocess.call(cmd)
    if status == 0:
        click.secho('build_one: Docker build succeeded.',
                    fg='green')
    else:
        click.secho('build_one: Docker build failed with %d' % status,
                    fg='red')
        raise click.Abort()


def show_docker_images(repo):
    cmd = ['docker', 'images', repo]
    return subprocess.call(cmd)


def get_filename_from_base_image(base_image):
    return 'Dockerfile-' + base_image


def get_tag_from_base_image(base_image):
    tag = base_image
    replacements = {'python:': 'py', '-onbuild': ''}

    for old, new in replacements.items():
        tag = tag.replace(old, new)

    return tag


if __name__ == '__main__':
    pydockerize()
