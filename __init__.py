#!/usr/bin/python3
# copyright (c) 2018- polygoniq xyz s.r.o.

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import os
import sys
import typing
import bpy
import subprocess


bl_info = {
    "name": "Open Linked",
    "author": "polygoniq xyz s.r.o.",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "Right-click context menu for libraries in Outliner",
    "description": "Open linked blends from the Outliner",
    "category": "Interface",
}


ADDON_CLASSES: typing.List[typing.Type] = []


class OpenBlendFromOutliner(bpy.types.Operator):
    bl_idname = "open_linked.open"
    bl_label = "Open Linked Blends"
    bl_description = "Open selected linked .blend files in new Blender instances"

    @staticmethod
    def get_selected_libs(context: bpy.types.Context) -> typing.List[bpy.types.Library]:
        """Returns libraries selected in the Outliner."""
        return [o for o in context.selected_ids if isinstance(o, bpy.types.Library)]

    def execute(self, context: bpy.types.Context):
        selected_libs = OpenBlendFromOutliner.get_selected_libs(context)
        if len(selected_libs) == 0:
            self.report({'ERROR'}, "No linked .blend files selected")
            return {'CANCELLED'}

        for selected_lib in selected_libs:
            linked_blend_path = os.path.realpath(bpy.path.abspath(selected_lib.filepath))
            if not os.path.isfile(linked_blend_path):
                self.report(
                    {'WARNING'}, f"Linked blend '{selected_lib.filepath}' does not exist, skipping.")
                continue

            blender_executable = bpy.app.binary_path
            args = [blender_executable, linked_blend_path]

            if sys.platform in ["win32", "cygwin"]:
                # Detach child process and close its stdin/stdout/stderr, so it can keep running
                # after parent Blender is closed.
                # https://stackoverflow.com/questions/52449997/how-to-detach-python-child-process-on-windows-without-setsid
                flags = 0
                flags |= subprocess.DETACHED_PROCESS
                flags |= subprocess.CREATE_NEW_PROCESS_GROUP
                flags |= subprocess.CREATE_NO_WINDOW
                subprocess.Popen(args, close_fds=True, creationflags=flags)
            elif sys.platform in ["darwin", "linux", "linux2"]:  # POSIX systems
                subprocess.Popen(args, start_new_session=True)
            else:
                raise RuntimeError(f"Unsupported OS: sys.platform={sys.platform}")

        return {'FINISHED'}


ADDON_CLASSES.append(OpenBlendFromOutliner)


def draw_outliner_tools(self, context: bpy.types.Context) -> None:
    """Adds operators to Outliner right-click menu."""
    if len(OpenBlendFromOutliner.get_selected_libs(context)) > 0:
        self.layout.separator()
        self.layout.operator(OpenBlendFromOutliner.bl_idname, icon='FILE_FOLDER')


def register():
    for cls in ADDON_CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.OUTLINER_MT_context_menu.append(draw_outliner_tools)


def unregister():
    bpy.types.OUTLINER_MT_context_menu.remove(draw_outliner_tools)
    for cls in reversed(ADDON_CLASSES):
        bpy.utils.unregister_class(cls)

    # Remove all nested modules from module cache, more reliable than importlib.reload(..)
    # Idea by BD3D / Jacques Lucke
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(__name__):
            del sys.modules[module_name]
