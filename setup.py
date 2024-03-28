from setuptools import setup, find_packages
from os.path import dirname, abspath
from rideology2gpx_tool.app_info import (version, author, author_email,
    description, app_name, author_user, repo_url)



base_dir = dirname(abspath(__file__))


# Get the long description from README.md
with open(base_dir + "/README.md", "r") as file_:
    long_description = file_.read()


# Fix some links in the long description
long_description = long_description.replace(
    "](" + repo_url + ")",
    "](" + repo_url + "/tree/v" + version + ")"
)
long_description = long_description.replace(
    "](docs/",
    "](" + repo_url + "/blob/v" + version + "/docs/"
)
long_description = long_description.replace(
    "![](images/",
    f"![](https://raw.githubusercontent.com/{author_user}/{app_name}/main/images/"
)


# Get the list of requirements
requirements = []
requires_files = ["/requirements.txt",
                  "/" + app_name + ".egg-info/requires.txt"]
for file_path in requires_files:
    try:
        with open(base_dir + file_path, "r") as file_:
            for p in file_.read().split():
                if p not in requirements:
                    requirements.append(p)
    except FileNotFoundError:
        pass
if not requirements:
    raise(Exception('Empty requirements!'))


setup(
    name=app_name ,
    version=version,
    packages=find_packages(),
    author=author,
    author_email=author_email,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Programming Language :: Python :: 3'
    ],
    python_requires='>=3.6',
    install_requires=requirements,
    scripts=[app_name]
)
