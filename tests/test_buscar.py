from src.buscar import filtrar, relevancia, palabras
from src.fuentes import _num


def r(tienda, nombre, precio):
    return {"tienda": tienda, "nombre": nombre, "precio": precio, "precio_antes": precio, "nota": "", "url": ""}


def test_num():
    assert _num("$ 1.299.900") == 1299900
    assert _num("269.900") == 269900


def test_relevancia_tolera_plurales_y_modelos():
    q = [w for w in palabras("audifonos jbl tune 520")]
    assert relevancia(q, "Audífonos JBL Tune 520BT Negro") == 1
    assert relevancia(q, "JBL Tune 520BT") == 0.75
    assert relevancia(q, "Audífonos Sony WH-CH520") == 0.25


def test_filtrar_quita_accesorios_irrelevantes_y_duplicados():
    res = [
        r("Éxito", "Audífonos JBL Tune 520BT Negro", 199900),
        r("Éxito", "Audífonos JBL Tune 520BT Negro", 199900),
        r("Alkosto", "Audífonos JBL Tune 520BT Azul", 189900),
        r("Amazon", "Almohadillas de repuesto para JBL Tune 520", 39000),
        r("Falabella", "Audífonos Sony WH-CH520", 150000),
        r("Ktronix", "Audifonos JBL Tune 520 BT", 195000),
        r("Olímpica", "JBL Tune 520BT audifonos", 9000),       # precio absurdo
    ]
    out = filtrar(res, "audifonos jbl tune 520")
    assert [x["tienda"] for x in out] == ["Alkosto", "Ktronix", "Éxito"]


def test_numero_de_modelo_obligatorio():
    q = palabras("audifonos jbl tune 520")
    assert relevancia(q, "JBL Audifonos Tune 530C") == 0
    assert relevancia(q, "JBL Audifonos Tune 5200") == 0
    assert relevancia(q, "JBL JBLT520BTBLUAM-Z Tune 520BT Auriculares") > 0
    assert relevancia(q, "Audífonos JBL Tune 520C USB-C") == 1
