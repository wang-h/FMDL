# -*- CMakeLists.txt. Do not edit by hand -*-
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

cmake_minimum_required(VERSION 3.5.1)
project(SuffixArray)

find_package(PythonLibs 3 REQUIRED)
find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})
include(GenerateExportHeader)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${PROJECT_BINARY_DIR}
    ${PYTHON_INCLUDE_PATH}
)


# Compiler options
add_definitions(-w)
add_definitions(-g)
add_definitions(-std=c++11) 
add_definitions(-Wall)
add_definitions(-O3)
add_definitions(-DNDEBUG) 
set(CMAKE_SWIG_OUTDIR ${CMAKE_CURRENT_BINARY_DIR}/../)
#
set(CMAKE_LDFLAGS "${CMAKE_LDFLAGS} -L. ")

if(WIN32)
    enable_language(RC)
    set(CMAKE_RC_COMPILE_OBJECT
        "<CMAKE_RC_COMPILER> ${RC_OPTIONS} -O coff -i <SOURCE> -o <OBJECT>")
endif(WIN32)
set(Boost_USE_STATIC_LIBS OFF) 
set(Boost_USE_STATIC_RUNTIME OFF) 

set(SUFFIXARRAY_SRCS
    drittel.cc
)

set(INTERFACE_FILES
    drittel.i
)

set_source_files_properties(${INTERFACE_FILES} PROPERTIES CPLUSPLUS   ON)
swig_add_library(drittel LANGUAGE python SOURCES ${INTERFACE_FILES}
    ${SUFFIXARRAY_SRCS}
)
swig_link_libraries(drittel
    ${PYTHON_LIBRARIES}
)
