"""
\********************************************************************************
* Copyright (c) 2023 the Qrisp authors
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* This Source Code may also be made available under the following Secondary
* Licenses when the conditions for such availability set forth in the Eclipse
* Public License, v. 2.0 are satisfied: GNU General Public License, version 2
* with the GNU Classpath Exception which is
* available at https://www.gnu.org/software/classpath/license.html.
*
* SPDX-License-Identifier: EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0
********************************************************************************/
"""
from typing import Optional, List

"""
This file sets up a client adhering to the interface specified by the Qunicorn middleware
developed in the SeQuenC project: https://sequenc.de/

To learn more about Qunicorn check out the Qunicorn GitHub: https://github.com/qunicorn/qunicorn-core
And it's documentation:
https://qunicorn-core.readthedocs.io/en/latest/index.html


"""
import requests
import time


class BackendClient:
    """
    This object allows connecting to Qunicorn backend servers.

    Parameters
    ----------
    socket_ip : string
        The IP address of the socket of the target server.
    port : int
        The port on which the server is listening.


    Examples
    --------

    We assume that the example from BackendServer has been executed in the same console.

    >>> from qrisp.interface import BackendClient
    >>> example_backend = BackendClient(api_endpoint = "127.0.0.1", port = 8080)
    >>> from qrisp import QuantumCircuit
    >>> qc = QuantumCircuit(2)
    >>> qc.h(0)
    >>> qc.cx(0,1)
    >>> qc.measure(qc.qubits)
    >>> example_backend.run(qc, shots = 1000)
    {'00': 510, '11': 490}

    """

    def __init__(
        self, api_endpoint: str, provider: str, device: str, port=None, token=""
    ):
        # https anstatt http
        api_endpoint = "http://" + api_endpoint
        # if api_endpoint[:8] != 'http://':
        #    api_endpoint = 'http://' + api_endpoint

        self.provider = provider
        self.device = device

        if port is None:
            port = 9010

        self.port = port
        self.token = token

        self.api_endpoint = api_endpoint + ":" + str(port)

    # Executes
    def run(self, qc, shots):
        qasm_str = qc.qasm()

        deployment_data = {
            "programs": [
                {
                    "quantumCircuit": qasm_str,
                    "assemblerLanguage": "QASM2",
                    "pythonFilePath": "",
                    "pythonFileMetadata": "",
                }
            ],
            "name": "",
        }
        deployment_response = requests.post(
            f"{self.api_endpoint}/deployments", json=deployment_data, verify=False
        )

        if deployment_response.status_code == 422:
            raise Exception(
                f"Unprocessable quantum circuit {deployment_response.status_code}"
            )
        elif deployment_response.status_code != 201:
            print(deployment_response.status_code)
            raise Exception(
                f"Failed to deploy quantum circuit {deployment_response.status_code}"
            )

        deployment_id = deployment_response.json()["id"]

        job_data = {
            "name": "",
            "providerName": self.provider,
            "deviceName": self.device,
            "shots": shots,
            "token": self.token,
            "type": "RUNNER",
            "deploymentId": deployment_id,
        }

        job_post_response = requests.post(
            f"{self.api_endpoint}/jobs", json=job_data, verify=False
        )
        if job_post_response.status_code == 422:
            raise Exception(
                f"Unprocessable job (status code: {job_post_response.status_code})"
            )
        elif job_post_response.status_code != 201:
            raise Exception(
                f"Failed to post job (status code: {job_post_response.status_code})"
            )

        job_id = job_post_response.json()["id"]

        while True:
            job_get_response = requests.get(
                f"{self.api_endpoint}/jobs/{job_id}", json=job_data, verify=False
            )

            if job_get_response.status_code != 200:
                raise Exception(
                    f'Quantum circuit execution failed: {job_get_response.json()["message"]}'
                )

            job_state = job_get_response.json()["state"]

            if job_state == "FINISHED":
                break

            time.sleep(0.1)

        for job_result in job_get_response.json()["results"]:
            if job_result["resultType"] == "COUNTS":
                counts = job_result["data"]
                metadata = job_result["metadata"]
                counts_format = metadata["format"]
                registers: List[int] | None = None

                if counts_format == "hex":
                    registers = [r["size"] for r in metadata["registers"]]

                counts_binary = {
                    self._ensure_binary(
                        k, job_result["metadata"]["format"], registers
                    ): v
                    for k, v in counts.items()
                }

                return counts_binary

        raise ValueError("No COUNTS result type in job response")

    @staticmethod
    def _ensure_binary(
        result: str, counts_format: str, registers: Optional[list[int]]
    ) -> str:
        if counts_format == "bin":
            return result  # result is already binary
        elif counts_format == "hex":
            if registers is None:
                raise ValueError("Parameter registers is required for hex values!")

            register_counts = result.split()

            return "".join(
                f"000{int(val, 16):b}"[-size:]
                for val, size in zip(register_counts, registers)
            )
        else:
            raise ValueError(f"Unknown format {counts_format}")
