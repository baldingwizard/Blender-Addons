# Blender-Addons

These add-ons are provided free to use for whatever purpose. However, if you do find them useful and wish to show your appreciation then please consider sending a donation to https://www.paypal.me/BaldingWizard. Any donation will be received with thanks and a pledge to return a proportionate amount of effort back into the Blender community.


MathsExpression
===============
Download : https://github.com/baldingwizard/Blender-Addons/raw/master/MathsExpression.zip

Allows you to simply type an equation and the add-on automatically builds the node tree for you using standard maths nodes. This allows a complicated tree to be very easily constructed and is still fully GPU compatible (since it's only using 'standard' nodes).

The following operations are currently supported :

Addition, Subtraction, Multiply, Divide, Power, Sine, Cosine, Tangent, Arcsine, Arccosine, Arctangent, Absolute, Round, Greater Than, Less Than, Greater Than or Equals, Less Than or Equals, Equals, Maximum, Minimum, Modulo, Log, atan2(x,y)

The tree is implemented as a Group but the node is displayed as a standard node. However, it is possible to get your hands on the actual node tree of the 'inner' workings via the standard 'Group' node. The node tree can be automatically layed out but this needs some additional refining so this feature will be disabled in the initial versions of the add-on (ie, only creation of the tree, no easy access to the internals). Future versions are planned to include options to 'ungroup' the nodes if desired.

Limitations
-----------
Note that the add-on does not currently trap more than the required number of inputs to a function - ie, `sin(x,y)` is treated as valid - the second input is still passed to the Maths node but will have no effect (since 'sine' only takes a single input). Similarly, with more than two inputs the additional inputs are not currently processed - so `sin(x,y,z)` will be accepted but treated as `sin(x)`.

Future Development
------------------
* Better syntax trapping and reporting with meaningful messages
* Handling of incorrect number of arguments
* Enhance Max, Min, Add, Subtract, Multiply, Divide to accept (and process) any number of arguments (eg, `max(a,b,c,d,e,f)`)
* Add-on settings to allow 'debug' mode to be enabled/disabled (access to the node tree)
* Better layout of the nodes in the group (mostly works at present but can result in overlapping nodes)
* Create documentation page
* Handle constants - eg, 'pi' (currently interpreted as an input)
* Support multiple equations per node - eg, `dist=(x**2+y**2+z**2)**0.5,biggest=max(x,y,z)`
* Allow such sub-values to be used as inputs - eg, `dist=(x**2+y**2+z**2)**0.5,biggest=max(x,y,z),combined=dist*biggest`
* Allow such sub-values to be hidden from the 'output' - eg, by prefixing name with `_`
