import io
import zipfile
from pathlib import Path

import pytest
import responses

from src.ingestion.ans_client import BASE_URL, Competencia, baixar_trimestre, montar_url


def test_competencia_rejeita_trimestre_invalido():
    with pytest.raises(ValueError):
        Competencia(ano=2024, trimestre=5)


def test_competencia_rejeita_ano_antigo():
    with pytest.raises(ValueError):
        Competencia(ano=2005, trimestre=1)


def test_montar_url_segue_padrao_da_ans():
    url = montar_url(Competencia(ano=2024, trimestre=1))
    assert url == f"{BASE_URL}/2024/1T2024.zip"


def _zip_com(arquivos: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for nome, conteudo in arquivos.items():
            zf.writestr(nome, conteudo)
    return buf.getvalue()


@responses.activate
def test_baixar_trimestre_extrai_apenas_csv(tmp_path: Path):
    comp = Competencia(ano=2024, trimestre=1)
    corpo = _zip_com({"1T2024.csv": b"REG_ANS;DATA\n123;2024-03-31\n", "leia-me.pdf": b"%PDF"})
    responses.add(responses.GET, montar_url(comp), body=corpo, status=200)

    extraidos = baixar_trimestre(comp, tmp_path)

    assert [p.name for p in extraidos] == ["1T2024.csv"]
    assert extraidos[0].read_bytes().startswith(b"REG_ANS")


@responses.activate
def test_baixar_trimestre_falha_se_zip_sem_csv(tmp_path: Path):
    comp = Competencia(ano=2024, trimestre=2)
    responses.add(responses.GET, montar_url(comp), body=_zip_com({"nota.txt": b"x"}), status=200)

    with pytest.raises(RuntimeError, match="nenhum CSV"):
        baixar_trimestre(comp, tmp_path)
