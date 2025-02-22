To generate a .puml file from a portion of simpeg-drivers code we can use
pylint's pyreverse utility. The following command run from the current
directory will create a 'classes_gravity_options.puml' file with that
describes the gravity params class and its ancestors (base classes).

pyreverse --output puml --all-ancestors --project gravity_params ../simpeg_drivers/potential_fields/gravity/params.py

The .puml support will require a GraphViz installation, and in order to
visualize the .puml file within PyCharm, there needs to be a plantuml
installation (available on conda-forge) as well as the PlantUML integration
plugin for PyCharm.
