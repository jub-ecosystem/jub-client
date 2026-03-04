# Installation

<h2>Cloning the repository</h2>
Clone the Jub Client repository :
```
git clone https://github.com/jub-ecosystem/jub-client
```

Jub Client has a few requeriments:


- [Poetry](https://python-poetry.org/)

Install them with :

```
pipx install poetry
```
> [**pipx**](https://pipx.pypa.io/stable/) is used to install Python CLI applications globally while still isolating them in virtual environments. 

<h2>Installing dependencies</h2>
After you cloned the repository , you must navigate to the **jub-client** folder and install the project dependencies with **poetry** :

```
cd jub-client
poetry install
```

Now you should activate the virtual env : 
```
poetry self add poetry-plugin-shell
poetry shell
```


<h2>Running the project</h2>
```
chmod +x deploy.sh
./deploy.sh
```
This will deploy the services such as the API and database of the project.

Now you can run the test in the `tests/` folder :

```
coverage run -m pytest tests/
```
