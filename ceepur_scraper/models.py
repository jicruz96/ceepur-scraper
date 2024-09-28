from typing import Literal, Union

import xmltodict
from aiohttp import ClientResponse

VoterStatus = Literal[
    "A",  # Activo
    "I",  # Inactivo
    "E",  # Excluido
]


class PublicVoterRecord:
    def __init__(
        self,
        NumeroElectoral: int,
        Precinto: int,
        Unidad: int,
        FechaNacimiento: str,
        Status: VoterStatus,
        Category: str,
        Municipio: str,
        EstatusDescripcion: str,
        CategoriaDescripcion: str,
        Colegio: int,
        Tomo: int,
        Linea: int,
    ):
        self.NumeroElectoral = NumeroElectoral
        self.Precinto = Precinto
        self.Unidad = Unidad
        self.FechaNacimiento = FechaNacimiento
        self.Status = Status
        self.Category = Category
        self.Municipio = Municipio
        self.EstatusDescripcion = EstatusDescripcion
        self.CategoriaDescripcion = CategoriaDescripcion
        self.Colegio = Colegio
        self.Tomo = Tomo
        self.Linea = Linea

    @classmethod
    async def parse_ceepur_api_response(cls, response: ClientResponse) -> Union["PublicVoterRecord", None]:
        response.raise_for_status()

        data = xmltodict.parse(await response.text())["Elector"]
        # A voter ID of 0 is CEE's way of saying this voter ID doesn't exist
        if data["NumeroElectoral"] == "0":
            return None
        return cls(
            NumeroElectoral=int(data["NumeroElectoral"]),
            Precinto=int(data["Precinto"]),
            Unidad=int(data["Unidad"]),
            FechaNacimiento=data["FechaNacimiento"],
            Status=data["Status"],
            Category=data["Category"],
            Municipio=data["Municipio"],
            EstatusDescripcion=data["EstatusDescripcion"],
            CategoriaDescripcion=data["CategoriaDescripcion"],
            Colegio=int(data["Colegio"]),
            Tomo=int(data["Tomo"]),
            Linea=int(data["Linea"]),
        )
