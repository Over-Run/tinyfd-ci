cmake_minimum_required(VERSION 3.15)
project(tinyfd VERSION 3.21.2 LANGUAGES C)

# Options
option(BUILD_SHARED_LIBS "Build tinyfd as shared library" ON)
option(TINYFD_BUILD_EXAMPLES "Build example programs" OFF)
option(TINYFD_BUILD_TESTS "Build test programs" OFF)
option(TINYFD_INSTALL "Generate install targets" ON)
option(TINYFD_ENABLE_WARNINGS "Enable extra compiler warnings" ON)
option(TINYFD_ENABLE_OPTIMIZATIONS "Enable compiler optimizations (Release-like)" ON)

# C standard
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Output directories
# Put runtime artifacts and libraries into the build tree under bin/ and lib/
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

# Source and include directory variables (default to project directory)
set(TINYFD_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}" CACHE PATH "Directory containing tinyfd source files")
set(TINYFD_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}" CACHE PATH "Directory containing tinyfd header files")

# Prefer conventional src/ and include/ subdirectories if they exist
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src")
    set(TINYFD_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src" CACHE PATH "Directory containing tinyfd source files" FORCE)
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/include")
    set(TINYFD_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include" CACHE PATH "Directory containing tinyfd header files" FORCE)
endif()

# Require an explicit semicolon-separated list of source files.
# Do NOT use globbing or auto-discovery. Provide paths relative to the
# project root or absolute paths. Example: -DTINYFD_SOURCE_FILES="src/a.c;src/b.c"
set(TINYFD_SOURCE_FILES "tinyfiledialogs.c" CACHE STRING "Semicolon-separated list of source files for tinyfd (required).")

# Fail early if the user didn't provide any source files — no auto-discovery allowed.
if(NOT TINYFD_SOURCE_FILES)
    message(FATAL_ERROR "TINYFD_SOURCE_FILES is empty. Please set it to a semicolon-separated list of source files (no GLOB_RECURSE or discovery).")
endif()

# Convert the semicolon-separated cache string into a CMake list and validate files.
# Convert the semicolon-separated cache string into a CMake list and resolve
# each entry to an absolute path (relative paths are resolved against the
# project source directory). Validate existence and build the final list.
set(TINYFD_SOURCE_LIST ${TINYFD_SOURCE_FILES})
set(TINYFD_SOURCES "")
foreach(_src IN LISTS TINYFD_SOURCE_LIST)
    if(NOT IS_ABSOLUTE "${_src}")
        set(_abs_src "${CMAKE_CURRENT_SOURCE_DIR}/${_src}")
    else()
        set(_abs_src "${_src}")
    endif()

    if(NOT EXISTS "${_abs_src}")
        message(FATAL_ERROR "Source file '${_src}' (resolved to '${_abs_src}') listed in TINYFD_SOURCE_FILES does not exist.")
    endif()

    list(APPEND TINYFD_SOURCES "${_abs_src}")
endforeach()

add_library(tinyfd ${TINYFD_SOURCES})

target_include_directories(tinyfd PUBLIC
    $<BUILD_INTERFACE:${TINYFD_INCLUDE_DIR}>
    $<INSTALL_INTERFACE:include>
)

if(WIN32)
    target_link_libraries(tinyfd PRIVATE comdlg32 ole32)
endif()

if(TINYFD_ENABLE_WARNINGS)
    if(MSVC)
        target_compile_options(tinyfd PRIVATE /W4 /permissive-)
    else()
        target_compile_options(tinyfd PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endif()

# Enable optimizations when requested and only for Release-like configurations.
# This supports both single-config generators (checks CMAKE_BUILD_TYPE) and
# multi-config generators via generator expressions ($<CONFIG:...>).
if(TINYFD_ENABLE_OPTIMIZATIONS)
    # Helper generator expressions for config-aware flags
    if(MSVC)
        # Apply /O2 for Release and RelWithDebInfo
        target_compile_options(tinyfd PRIVATE
            $<$<OR:$<CONFIG:Release>,$<CONFIG:RelWithDebInfo>>:/O2>
        )
        # For single-config generators, also respect CMAKE_BUILD_TYPE variable
        if(NOT CMAKE_CONFIGURATION_TYPES)
            if(CMAKE_BUILD_TYPE STREQUAL "Release" OR CMAKE_BUILD_TYPE STREQUAL "RelWithDebInfo")
                string(APPEND CMAKE_C_FLAGS " /O2")
            endif()
        endif()
    else()
        # Apply -O3 (and optionally -flto) for Release and RelWithDebInfo
        target_compile_options(tinyfd PRIVATE
            $<$<OR:$<CONFIG:Release>,$<CONFIG:RelWithDebInfo>>:-O3>
        )

        # Check for -flto support and add it in a config-aware manner
        include(CheckCCompilerFlag)
        check_c_compiler_flag("-flto" COMPILER_SUPPORTS_FLTO)
        if(COMPILER_SUPPORTS_FLTO)
            target_compile_options(tinyfd PRIVATE
                $<$<OR:$<CONFIG:Release>,$<CONFIG:RelWithDebInfo>>:-flto>
            )
        endif()

        # Single-config fallback: if using a single-config generator and the
        # build type is a release-like type, append flags to CMAKE_C_FLAGS
        if(NOT CMAKE_CONFIGURATION_TYPES)
            if(CMAKE_BUILD_TYPE STREQUAL "Release" OR CMAKE_BUILD_TYPE STREQUAL "RelWithDebInfo")
                string(APPEND CMAKE_C_FLAGS " -O3")
                if(COMPILER_SUPPORTS_FLTO)
                    string(APPEND CMAKE_C_FLAGS " -flto")
                endif()
            endif()
        endif()
    endif()
endif()

if(TINYFD_INSTALL)
    install(TARGETS tinyfd
        EXPORT tinyfdTargets
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
    # Install headers from the configured include directory
    install(DIRECTORY "${TINYFD_INCLUDE_DIR}/" DESTINATION include)
    install(EXPORT tinyfdTargets FILE tinyfdTargets.cmake NAMESPACE tinyfd:: DESTINATION lib/cmake/tinyfd)
endif()

# Optional subdirectories
if(TINYFD_BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

if(TINYFD_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
