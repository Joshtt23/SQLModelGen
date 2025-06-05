import jinja2
import os

def test_model_template_renders():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates')))
    template = env.get_template('model.jinja2')
    rendered = template.render(class_name="User", fields=["id: int"], relationships=[], extra_imports=[])
    assert "class User" in rendered

def test_enum_template_renders():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates')))
    template = env.get_template('enum.jinja2')
    rendered = template.render(enum_name="UserStatus", values=["active", "inactive"])
    assert "class UserStatus" in rendered 