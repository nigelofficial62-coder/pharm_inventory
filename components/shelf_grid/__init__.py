import os
import streamlit.components.v1 as components

# Get the absolute path to the directory containing this file
parent_dir = os.path.dirname(os.path.abspath(__file__))

# Declare the component
_component_func = components.declare_component("shelf_grid", path=parent_dir)

def shelf_grid(html_grid, css_string="", key=None):
    """
    Renders the custom shelf grid and returns the clicked bin data.
    """
    component_value = _component_func(
        html_grid=html_grid,
        css_string=css_string,
        key=key,
        default=None
    )
    return component_value
