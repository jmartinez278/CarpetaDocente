"""Almacén de prueba que firma como el de Vercel (design de US-011, D7).

Es ``S3Storage`` con credenciales ficticias: botocore firma el enlace en el propio proceso, sin
conectarse a R2. Guarda cada llamada a ``url`` para revisar sus argumentos.
"""

from storages.backends.s3 import S3Storage

ENDPOINT = "https://cuenta-ficticia.r2.cloudflarestorage.com"


class AlmacenQueFirma(S3Storage):
    llamadas: list = []

    def __init__(self, **opciones):
        super().__init__(
            access_key="clave-ficticia",
            secret_key="secreto-ficticio",  # noqa: S106 - credencial de prueba, no real
            bucket_name="sesiones-prueba",
            endpoint_url=ENDPOINT,
            region_name="auto",
            default_acl=None,
            querystring_auth=True,
            custom_domain=None,
            **opciones,
        )

    def url(self, name, parameters=None, expire=None, http_method=None):
        AlmacenQueFirma.llamadas.append({"name": name, "parameters": parameters, "expire": expire})
        return super().url(name, parameters=parameters, expire=expire, http_method=http_method)
