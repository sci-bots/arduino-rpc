from __future__ import absolute_import
from __future__ import print_function
import re
import os
import shutil

from paver.easy import task, needs, path, sh, cmdopts, options


prefix = 'arduino_rpc.pavement_base.'
LIB_GENERATE_TASKS = [prefix + h for h in
                      ('generate_arduino_library_properties', )]
LIB_CMDOPTS = [('lib_out_dir=', 'o', 'Output directory for Arduino library.')]


def install_arduino_library(options):
    """Overrides install to copy Arduino library to sketch library directory."""
    import logging
    from arduino_helpers import sketchbook_directory

    arduino_lib_source = verify_library_directory(options)
    arduino_lib_destination = (path(sketchbook_directory())
                               .joinpath('libraries', arduino_lib_source.name))
    recursive_overwrite(arduino_lib_source, arduino_lib_destination)
    logging.info('Copied %s to %s' % (arduino_lib_source,
                                      arduino_lib_destination))


def recursive_overwrite(src, dest, ignore=None):
    '''
    http://stackoverflow.com/questions/12683834/how-to-copy-directory-recursively-in-python-and-overwrite-all#15824216
    '''
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            path(dest).makedirs_p()
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                recursive_overwrite(os.path.join(src, f),
                                    os.path.join(dest, f),
                                    ignore)
    else:
        shutil.copyfile(src, dest)


def verify_library_directory(options):
    '''
    Must be called from task function accepting `LIB_CMDOPTS` as `cmdopts`.
    '''
    import inspect

    from clang_helpers.data_frame import underscore_to_camelcase

    calling_function_name = inspect.currentframe().f_back.f_code.co_name
    default_lib_dir = options.rpc_module.get_lib_directory()

    if hasattr(options, calling_function_name):
        cmd_opts = getattr(options, calling_function_name)
        output_dir = path(getattr(cmd_opts, 'lib_out_dir', default_lib_dir))
    else:
        output_dir = default_lib_dir
    if 'camelcase_name' in options.LIB_PROPERTIES:
        camel_name = options.LIB_PROPERTIES['camelcase_name']
    else:
        name = options.LIB_PROPERTIES['package_name'].replace('-', '_')
        camel_name = underscore_to_camelcase(name)
    library_dir = output_dir.joinpath(camel_name)
    library_dir.makedirs_p()
    return library_dir


@task
@cmdopts(LIB_CMDOPTS, share_with=LIB_GENERATE_TASKS)
def generate_arduino_library_properties(options):
    '''
    .. versionchanged:: X.X.X
        Read template file as text (not binary) to support Python 3.
    '''
    import jinja2
    import arduino_rpc

    from clang_helpers.data_frame import underscore_to_camelcase

    with (arduino_rpc.get_library_directory()
          .joinpath('library.properties.t').open('r')) as input_:
        template_str = input_.read()

    template = jinja2.Template(template_str)
    library_dir = verify_library_directory(options)
    library_properties = library_dir.joinpath('library.properties')
    name = options.LIB_PROPERTIES['package_name']
    camel_name = underscore_to_camelcase(name)
    version = re.sub(r'[^\d\.]+', '',
                     options.LIB_PROPERTIES.get('version', '0.1.0'))
    version = re.sub(r'^([^\.]+.[^\.]+.[^\.]+)\..*', r'\1', version)
    with library_properties.open('wb') as output:
        output.write(template.render(camel_name=camel_name,
                                     lib_version=version,
                                     **options.LIB_PROPERTIES))


@task
@cmdopts(LIB_CMDOPTS, share_with=LIB_GENERATE_TASKS)
def copy_existing_headers(options):
    project_lib_dir = verify_library_directory(options)
    source_dir = options.rpc_module.get_lib_directory()
    output_dir = project_lib_dir.parent
    if source_dir == output_dir:
        print('Output library directory is same as source - do not copy.')
    else:
        print('Output library directory differs from source - copy.')
        recursive_overwrite(source_dir, output_dir)


@task
@cmdopts(LIB_CMDOPTS, share_with=LIB_GENERATE_TASKS)
@needs('copy_existing_headers', 'generate_arduino_library_properties')
def build_arduino_library(options):
    import zipfile

    library_dir = verify_library_directory(options)
    zf = zipfile.ZipFile(library_dir + '.zip', mode='w')

    for f in library_dir.walkfiles():
        zf.write(f, arcname=library_dir.relpathto(f))
    zf.close()


@task
@needs('setuptools.command.install')
def install(options):
    """Override install to copy Arduino library to sketch library directory."""
    install_arduino_library(options)


@task
@needs('setuptools.command.develop')
def develop(options):
    """Override develop to copy Arduino library to sketch library directory."""
    install_arduino_library(options)


@task
@needs('wheel.bdist_wheel')
def bdist_wheel(options):
    """Override develop to copy Arduino library to sketch library directory."""
    install_arduino_library(options)
