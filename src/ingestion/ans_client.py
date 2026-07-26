"""Download dos dados abertos da ANS (demonstrações contábeis das operadoras).

Fonte pública, sem autenticação:
https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/

Os arquivos são ZIPs trimestrais com CSVs em latin-1 e separador ';'.
O padrão de URL pode mudar; ele fica isolado em BASE_URL e montar_url.
"""

from __future__ import annotations

import io
import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis"
TRIMESTRES_VALIDOS = (1, 2, 3, 4)


@dataclass(frozen=True)
class Competencia:
    ano: int
    trimestre: int

    def __post_init__(self) -> None:
        if self.trimestre not in TRIMESTRES_VALIDOS:
            raise ValueError(f"trimestre inválido: {self.trimestre}")
        if self.ano < 2010:
            raise ValueError(f"ano fora do histórico disponível: {self.ano}")

    @property
    def rotulo(self) -> str:
        return f"{self.trimestre}T{self.ano}"


def montar_url(comp: Competencia, base_url: str = BASE_URL) -> str:
    return f"{base_url}/{comp.ano}/{comp.rotulo}.zip"


def _sessao(retries: int = 5) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=2.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def baixar_trimestre(
    comp: Competencia,
    destino: Path,
    base_url: str = BASE_URL,
    session: requests.Session | None = None,
    timeout: int = 120,
) -> list[Path]:
    """Baixa o ZIP do trimestre e extrai os CSVs em destino/<rotulo>/.

    Devolve os caminhos extraídos. Idempotente: extração sobrescreve.
    """
    session = session or _sessao()
    url = montar_url(comp, base_url)
    LOGGER.info("baixando %s", url)

    resposta = session.get(url, timeout=timeout)
    resposta.raise_for_status()

    pasta = destino / comp.rotulo
    pasta.mkdir(parents=True, exist_ok=True)

    extraidos: list[Path] = []
    with zipfile.ZipFile(io.BytesIO(resposta.content)) as zf:
        for nome in zf.namelist():
            if not nome.lower().endswith(".csv"):
                continue
            alvo = pasta / Path(nome).name
            alvo.write_bytes(zf.read(nome))
            extraidos.append(alvo)
            LOGGER.info("extraído %s (%d bytes)", alvo.name, alvo.stat().st_size)

    if not extraidos:
        raise RuntimeError(f"nenhum CSV dentro de {url}")
    return extraidos
