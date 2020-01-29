# Copyright (C) 2016-2020 by the multiphenics authors
#
# This file is part of multiphenics.
#
# multiphenics is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# multiphenics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with multiphenics. If not, see <http://www.gnu.org/licenses/>.
#

import cppimport
import hashlib
import os
import sys
from pathlib import Path
from dolfinx import wrappers
from dolfinx.jit import dolfinx_pc, mpi_jit_decorator

@mpi_jit_decorator
def compile_code(package_name, package_code, **kwargs):
    # Set other sources
    try:
        sources = kwargs["sources"]
    except KeyError:
        sources = []
    
    # Set include file dependencies
    try:
        dependencies = kwargs["dependencies"]
    except KeyError:
        dependencies = []
        
    # Set include dirs
    try:
        include_dirs = kwargs["include_dirs"]
    except KeyError:
        include_dirs = []
    include_dirs.extend(dolfinx_pc["include_dirs"])
    include_dirs.append(str(wrappers.get_include_path()))
        
    # Set compiler arguments
    try:
        compiler_args = kwargs["compiler_args"]
    except KeyError:
        compiler_args = []
    compiler_args.append("-std=c++17")
    compiler_args.extend("-D" + dm for dm in dolfinx_pc["define_macros"])
        
    # Set libraries
    try:
        libraries = kwargs["libraries"]
    except KeyError:
        libraries = []
    libraries.extend(dolfinx_pc["libraries"])
        
    # Set library directories
    try:
        library_dirs = kwargs["library_dirs"]
    except KeyError:
        library_dirs = []
    library_dirs.extend(dolfinx_pc["library_dirs"])
        
    # Set linker arguments
    try:
        linker_args = kwargs["linker_args"]
    except KeyError:
        linker_args = []
        
    # Prepare cpp import file
    package_cppimport_code = f"""
/*
<%
setup_pybind11(cfg)
cfg['sources'] += {str(sources)}
cfg['dependencies'] += {str(dependencies)}
cfg['include_dirs'] += {str(include_dirs)}
cfg['compiler_args'] += {str(compiler_args)}
cfg['libraries'] += {str(libraries)}
cfg['library_dirs'] += {str(library_dirs)}
cfg['linker_args'] += {str(linker_args)}
%>
*/
"""

    # Compute hash from package name
    package_hash = hashlib.md5(package_code.encode("utf-8")).hexdigest()
    package_name_with_hash = package_name + "_" + package_hash
    
    # Write to cache directory
    cache_dir = str(Path(os.getenv("FENICS_CACHE_DIR", "~/.cache/fenics")).expanduser())
    os.makedirs(cache_dir, exist_ok=True)
    open(
        os.path.join(cache_dir, package_name_with_hash + ".cpp"), "w"
    ).write(
        package_cppimport_code + package_code.replace("SIGNATURE", package_name_with_hash)
    )
    
    # Append cache directory to path
    sys.path.append(cache_dir)
    
    # Return module generated by cppimport
    return cppimport.imp(package_name_with_hash)
