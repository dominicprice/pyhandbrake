# pyhandbrake - Python library to interface with HandBrakeCLI

pyhandbrake is a small wrapper around `HandBrakeCLI` which I wrote when
developing a project. Main features include:

* Fully typed models representing handbrake output
* Ability to load, modify and save presets
* Ability to scan and rip titles
* Live progress callbacks for supported commands

## Installation

You will need a working copy of HandBrakeCLI as it is not included in this
python package. For instructions on multiple OSes, see the [installation
guide](https://handbrake.fr/docs/en/1.2.0/get-handbrake/download-and-install.html).
For ubuntu based distributions, it can be obtained with `sudo apt-get install
handbrake-cli`.

### From PyPI

pyhandbrake is available on PyPI, simply run `pip install pyhandbrake`

### From the git repo

You can install python projects using pip directly from the git repo, in this instance with
`pip install git+https://github.com/dominicprice/pyhandbrake`

### From source

1. Clone the repo with `git clone https://github.com/dominicprice/pyhandbrake`
2. `cd` into the `pyhandbrake` directory
3. Run `pip install .`

## Usage

Although the package is named `pyhandbrake`, the actual name of the package you
should import is `handbrake` (a slightly confusing but common convention with
python packages). The package exposes one main object, `HandBrake`, which
contains methods for interacting the handbrake cli:

* `HandBrake.version(...)`
* `HandBrake.convert_title(...)`
* `HandBrake.scan_title(...)`
* `HandBrake.scan_all_titles(...)`
* `HandBrake.get_preset(...)`
* `HandBrake.list_presets(...)`
* `HandBrake.load_preset_from_file(...)`

Information about these function can be found in the docstrings on the methods,
found in [src/handbrake/__init__.py](src/handbrake/__init__.py) and information about the return types can
be found in the [src/handbrake/models](src/handbrake/models) directory.

### Passing arguments to `convert_title`

Rather than accept all possible command line arguments, `convert_title` only allows
you to set most options through a preset. Therefore you need to find out which
preset setting corresponds to the given command line argument and set that value
in a `Preset` object and add the preset to the search path by using it in the
`presets` parameter.

Note that you should name the preset something unique, and then tell handbrake
to use that preset by also passing the name to the `preset` argument, for
example:

```
from handbrake import HandBrake

h = HandBrake()
# get the default CLI preset, but could also use
# h.get_preset("<builtin preset name>") to get any
# of the inbuilt presets, or h.load_preset("<path to preset>")
# to load a custom preset
preset = h.get_preset("CLI Default")

# a preset contains layers which are held in the `preset_list` field. The default
# presets all contain one layer so we only do our work on `preset_list[0]`
preset.preset_list[0]["PictureWidth"] = 100
preset.preset_list[0]["PictureHeight"] = 50
preset.preset_list[0]["PresetName"] = "my_preset"

h.convert_title("/path/to/input", "/path/to/output", "main", preset="my_preset", presets=[preset])
```

### Handling progress updates

Methods related to reading titles accept a `ProgressHandler` argument. This
should be a function which accepts a `Progress` model, and it is called every
time handbrake emits a progress message allowing you to display information
about the progress of the command, e.g.

```
from handbrake import HandBrake
from handbrake.models import Progress

def progress_handler(p: Progress):
  print(p.task_description, f"{int(p.percent)}%")

h = HandBrake()
h.rip_title("/path/to/input", "/path/to/output", "main", progress_handler=progress_handler)
```


## Developing

pyhandbrake uses poetry as a toolchain. You should install poetry (via e.g.
`pipx install poetry`) and then inside the project root run `poetry install` to
create a virtual environment with all the dependencies.

Common project tasks are defined inside the Makefile:

* `make lint`: Run the mypy type checker
* `make format`: Run the code formatter
* `make test`: Run the test suite
* `make sdist`: Build the source distribution
* `make wheel`: Build a python wheel

## Troubleshooting

I do not really intend on actively maintaining this project unless I have to use
it again, so future versions of handbrake may introduce breaking changes. If you
notice this then pull requests would be very welcome! These notes are for future
me as much as they are for any other interested readers.

I anticipate that the most likely thing to cause errors/unexpected output is if
fields are added/removed/renamed from the JSON objects which handbrake outputs.

For added fields, pyhandbrake should silently ignore them - to include them you
will need to modify the relevant model in the [models](src/handbrake/models)
subpackage to include the field. Note that handbrake uses pascal case for field
names, but I have used snake case for the model field names. Pydantic
automatically takes care of converting between these naming conventions, but
will trip over capitalised abbreviations, (e.g. a field named `SequenceID`). In
this case, you need to assign a `Field` value to the field with the full name
handbrake uses as an alias parameter (e.g. `sequence_id: str =
Field(alias="SequenceID")`).

For fields which are removed/renamed, a pydantic validation error will be
emitted as the value would be required to populate the model. In this instance,
you should assign the value to a `Field` instance with a default value and the
deprecated flag (e.g. `old_field_name: str = Field("", deprecated=True)`). Note:
if the field is a mutable type then you will need to use a `default_factory`
instead of a value (e.g. `old_field_name: list[str] =
Field(default_factory=lambda: [], deprecated=True)`). If the field has been
renamed you can then create a new field with the new name as described in the
paragraph above.

A more pernicious problem would be if the output of the handbrake program
changes format. In this case the processing of the command output would need to
be rewritten, you are welcome to do so but the logic should still be able to
handle older versions of handbrake by i.e. checking the version and delegating
to an appropriate function.
