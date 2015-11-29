import natnetclient
import ratcave as rc
import numpy as np
import cliff_utills

from os import path
from psychopy import event, gui


# Note: Collect Metadata (subject, mainly, and Session Parameters) for the log
metadata = {'Experiment': 'Cliff_Avoidance',
            'Experimenter': 'Nicholas A. Del Grosso',
            'Rat': ['Test', 'Nessie', 'FuzzPatch', 'FlatWhite', 'Bridger'],
            'Cliff Depth': 1.5,
            'Cliff Side T-R, F-L': cliff_utills.read_and_pop_pickle_list('side_order_list.pickle')
            }

dlg = gui.DlgFromDict(metadata, 'Input Parameters:')
if not dlg.OK:
    sys.exit()

# Parameters
floor_depth = 1.5

# Connect to Motive and Set Rigid Bodies to Track
tracker = natnetclient.NatClient()
rat_rb = tracker.rigid_bodies['CalibWand']
arena_rb = tracker.rigid_bodies['Arena']

# Create Arena
arena_reader = rc.graphics.WavefrontReader(rc.graphics.resources.obj_arena)
arena = arena_reader.get_mesh('Arena', lighting=True, centered=False)

# Import Cliff Avoidance objects
reader = rc.graphics.WavefrontReader(path.join('Objects', 'CliffAvoidance.obj'))
vir_meshes = reader.get_meshes(['FakeArena', 'Board', 'DepthLeft', 'DepthRight'])
[vir_meshes[name].load_texture(rc.graphics.resources.img_uvgrid) for name in vir_meshes]  # Put an image texture on the walls and floors

# Use a Pseudo-Random order for determining which side the deep floor should be on.
floor_to_change = vir_meshes['DepthRight'] if metadata['Cliff Side T-R, F-L'] else vir_meshes['DepthLeft']
floor_to_change.local.y -= metadata['Cliff Depth']

# Realign everything to the arena, for proper positioning
additional_rotation = rc.utils.correct_orientation_natnet(arena_rb)
rc.utils.update_world_position_natnet(vir_meshes.values() + [arena], arena_rb, additional_rotation)

# Build ratCAVE Scenes
active_scene = rc.graphics.Scene([arena, vir_meshes['Board']], bgColor=(0., .3, 0., 1.),
                                 camera=rc.graphics.projector, light=rc.graphics.projector)

virtual_scene = rc.graphics.Scene(vir_meshes.values(), light=rc.graphics.projector, bgColor = (.1, 0., .1, 1.))
arena.cubemap = True

# Build ratCAVE Window
window = rc.graphics.Window(active_scene, screen=1, fullscr=True, virtual_scene=virtual_scene, shadow_rendering=False)

# Main Experiment Loop
tracker.wait_for_recording_start(debug_mode=metadata['Rat']=='Test')
with rc.graphics.Logger(scenes=[active_scene, virtual_scene], exp_name=metadata['Experiment'], log_directory=path.join('.', 'logs'),
                     metadata_dict=metadata) as logger:
    while 'escape' not in event.getKeys():
        virtual_scene.camera.position = rat_rb.position
        window.draw()
        logger.write()
        window.flip()