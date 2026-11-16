qt_add_executable(redpanda-git-askpass main.cpp)
set_target_properties(redpanda-git-askpass PROPERTIES MACOSX_BUNDLE OFF)

target_ui_classes(redpanda-git-askpass dialog)

target_compile_definitions(redpanda-git-askpass PRIVATE ${GLOBAL_COMPILE_DEFINITIONS})

target_link_libraries(redpanda-git-askpass PRIVATE
    Qt::Core
    Qt::Gui
    Qt::Widgets)

if(${FILESYSTEM_LAYOUT} STREQUAL "bundle")
    install(TARGETS redpanda-git-askpass
        RUNTIME DESTINATION RedPandaIDE.app/Contents/MacOS)
elseif(${FILESYSTEM_LAYOUT} STREQUAL "flat")
    install(TARGETS redpanda-git-askpass RUNTIME DESTINATION .)
else()
    install(TARGETS redpanda-git-askpass
        RUNTIME DESTINATION ${CMAKE_INSTALL_LIBEXECDIR}/${APP_NAME})
endif()
