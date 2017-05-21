import urllib
import json

from django import template

register = template.Library()

@register.filter
def index(List, i):
    return List[int(i)]

@register.filter
def getInt(value, arg):
    with urllib.request.urlopen("http://localhost:8000/patronaza/pridobiStevilko/" + str(arg) + "/" + str(value.id)) as url:
        data = json.loads(url.read().decode())
        return int(data["vrednost"])

    return 0

@register.filter
def getDate(value, arg):
    with urllib.request.urlopen("http://localhost:8000/patronaza/pridobiDatum/" + str(arg) + "/" + str(value.id)) as url:
        data = json.loads(url.read().decode())
        return data["vrednost"]

    return None

@register.filter
def getString(value, arg):
    with urllib.request.urlopen("http://localhost:8000/patronaza/pridobiNiz/" + str(arg) + "/" + str(value.id)) as url:
        data = json.loads(url.read().decode())
        return data["vrednost"]

    return ""