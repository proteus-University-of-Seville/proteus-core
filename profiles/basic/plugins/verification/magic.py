from proteus.views.components.abstract_component import ProteusComponent
from proteus.model.properties import Property

class Magic(ProteusComponent):
    """Iterate over all the objects in the archetype repository
    and store the name, category, tooltips, enum choices and classes
    in multiple sets. Then write the sets to a file.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print("Magic component initialized")
        self.do()

    def do(self):
        """Iterate over all the objects in the archetype repository
        and store the name, category, tooltips, enum choices and classes
        in multiple sets. Then write the sets to a file.
        """
        # Variables to store the names, categories, tooltips, enum choices and classes
        names = set()
        categories = set()
        tooltips = set()
        enum_choices = set()
        classes = set()

        # Get the archetype repository
        object_archetypes = self._controller._archetype_service._object_archetypes

        for category, class_dict in object_archetypes.items():
            for class_name, archetype_list in class_dict.items():
                for obj in archetype_list:
                    prop: Property
                
                    classes.update(obj.classes)

                    for prop_name, prop in obj.properties.items():
                        names.add(prop.name)
                        categories.add(prop.category)
                        
                        if prop.tooltip:
                            tooltips.add(prop.tooltip)

                        try:
                            if prop.choices:
                                enum_choices.update(prop.choices.split())
                        except AttributeError:
                            pass

        
        # Write to file
        with open("magic.txt", "w") as f:
            f.write("Names:\n")
            for name in names:
                f.write(f"{name}\n")
            f.write("\nCategories:\n")
            for category in categories:
                f.write(f"{category}\n")
            f.write("\nTooltips:\n")
            for tooltip in tooltips:
                f.write(f"{tooltip}\n")
            f.write("\nEnum Choices:\n")
            for enum_choice in enum_choices:
                f.write(f"{enum_choice}\n")
            f.write("\nClasses:\n")
            for class_name in classes:
                f.write(f"{class_name}\n")

        