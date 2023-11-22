# Auto-Hand-Rigger

A useful automatic hand rigger tool for maya artists who require a quick
and non-destructive hand rig. This tool utilizes linear interpolation between specified
joints. It provides artists with paintable finger-tip and palm selection areas to ensure
accurate joint interpolation locations. Further to this, the tool incorporates curve 
drawing capabilites whereby artists are expected to draw curves specifying joint chains 
with automatic mesh binding.

## Instructions on loading the tool

- Extract the src, Videos and images folder directory path to a local file path location
- Open the maya python editor.
- Copy and paste the main.py file within the src folder into the python editor
- This will prompt you with an empty field
- Copy and paste the directory path pointing to the file path location in step 1 into
  this empty field
- This will load the main user interface containing the paint joint controls and options

## Instructions on using the tool

### Paint context instructions

- To create the general hand rig you have toggle options outlining finger, knuckle
  and palm locations
- using the brush context paint each specified joint on your hand mesh, then tick the
  relative toggle associated with the joint you just painted. For example, if you
  paint finger 1, toggle the finger 1 checkbox.
- Repeat this step for all the joints, then click the apply button to see the automatic
  hand rig binded to the hand mesh.
- specify the amount of in between joints between knuckle and finger-tip landmark locations
  using the no. joints sliders and associated slider controls.
  
### Curve joint instructions

- To activate the curve joint controls, select the CV/Curve joints buttons
- This will pop-up with  separate brush context menu.
- Within this menu you have further artistic control over joint locations
- Joints will be created according to the stroke direction in which you paint
  using these curve tools.
  
## Further improvements
- Automatically weight painting hand joints binded to the hand mesh
- creating automatic IK/FK controls for the main hand joints
- ensuring that the tools works for hand meshes that are off-center and/or rotated
  in a random axis.
