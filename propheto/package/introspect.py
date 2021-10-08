from collections import defaultdict
from os.path import basename
from os import getcwd
import json
from time import sleep
from typing import Optional
from urllib.parse import urlparse, parse_qs, unquote
from typing import List
from pathlib import Path

# Below drawn from ipyparams package
_ipython_support = True

try:
    from IPython import get_ipython
    from IPython.display import display, Javascript
except ImportError:
    print("This package only works within Jupyter/IPython accessed from a browser.")
    _ipython_support = False


class Notebook:
    """
    Setting up Notebook Inference
    """

    def __init__(self, *args, **kwargs) -> None:
        self.filename = ""
        self.raw_url = ""
        self.params = defaultdict(lambda: None)
        self.raw_params = defaultdict(lambda: None)
        self.get_notebook_details()

    def get_notebook_details(self) -> None:
        """
        Get the name of the notebook
        """
        get_ipython().kernel.comm_manager.register_target(
            "url_querystring_target", self.target_func
        )
        sleep(0.2)
        # register the comm target on the browser side (front end)
        display(
            Javascript(
                """
            console.log('Starting front end url_querystring_target comm target');
            const comm = Jupyter.notebook.kernel.comm_manager.new_comm('url_querystring_target', {'init': 1});
            comm.send({'ipyparams_browser_url': window.location.href});
            console.log('Sent window.location.href on url_querystring_target comm target');
            comm.on_msg(function(msg) {
                console.log(msg.content.data);
            });
        """
            )
        )

    def update_params(self, url):
        self.raw_url = url
        parsed = urlparse(url)
        self.filename = unquote(basename(parsed.path))
        _raw_params = parse_qs(parsed.query)

        for k, v in _raw_params.items():
            self.params[k] = v[0]

        raw_params = _raw_params

    def target_func(self, comm, open_msg):
        # comm is the kernel Comm instance
        # open_msg is the comm_open message

        # register handler for later messages
        @comm.on_msg
        def _recv(msg):
            # data is in msg['content']['data']
            comm.send({"echo": msg["content"]["data"]})

            for k, v in msg["content"]["data"].items():
                if k == "ipyparams_browser_url":
                    self.update_params(v)

        # send data to the front end on creation
        comm.send({"init": 1})


class NotebookIntrospection(Notebook):
    """
    Introspect the jupyter notebook to parse code results.
    """

    def __init__(self, file_dir: Optional[str] = None, *args, **kwargs) -> None:
        super().__init__()
        self.notebook_contents = None
        self.notebook_code_cells = []
        self.file_dir = file_dir if file_dir else getcwd()
        self.notebook_log_cells = []
        self.notebook_pipeline_cells = []
        self.notebook_monitor_cells = []
        self.notebook_model_definition = []
        self.notebook_model_training = []

    def read_notebook(self, filepath: Optional[str] = None) -> dict:
        """
        Read the notebook and get the contents in a json file format
        """
        filepath = filepath if filepath else Path(self.file_dir, self.filename)
        with open(filepath, "r") as nb_file:
            file_content = nb_file.read()
        self.notebook_contents = json.loads(file_content)
        return self.notebook_contents

    def get_notebook_code_cells(self) -> List:
        """
        Get the code cells from the notebook
        """
        for cell in self.notebook_contents["cells"]:
            self.notebook_code_cells.append("".join(cell["source"]))
        return self.notebook_code_cells

    def _get_notebook_cell_types(self, cell_search_str: str) -> List:
        code_cells = []
        for cell in self.notebook_code_cells:
            if cell_search_str in cell:
                code_cells.append(cell)
        return code_cells

    def get_notebook_log_cells(self) -> List:
        """
        """
        notebook_log_cells = self._get_notebook_cell_types("propheto.log(")
        self.notebook_log_cells = notebook_log_cells
        return self.notebook_log_cells

    def get_notebook_data_pipeline_cells(self) -> List:
        """
        """
        notebook_pipeline_cells = self._get_notebook_cell_types("propheto.pipeline(")
        self.notebook_pipeline_cells = notebook_pipeline_cells
        return self.notebook_pipeline_cells

    def get_notebook_model_monitoring_cells(self) -> List:
        """
        """
        notebook_monitor_cells = self._get_notebook_cell_types("propheto.monitor(")
        self.notebook_monitor_cells = notebook_monitor_cells
        return self.notebook_monitor_cells

    def get_notebook_model_definition_cells(self) -> List:
        """
        """
        notebook_model_definition = self._get_notebook_cell_types(
            "propheto.model('define')"
        )
        self.notebook_model_definition = notebook_model_definition
        return self.notebook_model_definition

    def get_notebook_model_training_cells(self) -> List:
        """
        """
        notebook_model_training = self._get_notebook_cell_types(
            "propheto.model('train'"
        )
        self.notebook_model_training = notebook_model_training
        return self.notebook_model_training

    def __str__(self):
        return f"NotebookIntrospection(filename={self.filename})"

    def __repr__(self):
        return f"NotebookIntrospection(filename={self.filename})"


class PyFileIntrospect:
    def __init__(self, *args, **kwargs) -> None:
        pass


class CodeIntrospect(NotebookIntrospection):
    """
    
    """

    def __init__(self, file_dir: Optional[str] = None, *args, **kwargs) -> None:
        # TODO: Abstract methods and determine file type to introspect
        super().__init__()
        self.file_dir = file_dir if file_dir else getcwd()
        self.filename = ""

    def __str__(self):
        return f"CodeIntrospect(filename={self.filename})"

    def __repr__(self):
        return f"CodeIntrospect(filename={self.filename})"

