class TaborClientException(Exception):
    pass


class TaborClientSocketException(TaborClientException):
    def __init__(
        self,
        *args: object,
        code: int = -1,
    ) -> None:
        """A tabor client socket exception

        Args:
            code (int, optional): The execption code as returned from the
                Tabor machine. Defaults to -1.
        """
        if code is None:
            code = -1
        if not isinstance(code, int):
            try:
                code = int(code)
            except Exception:
                pass
        if code > -1:
            args = list(args) + [code]
        super().__init__(*args)
        self.code = code

    def __str__(self) -> str:
        val = super().__str__()
        if self.code > 0:
            val = f"{val} (code: {self.code})"
        return super().__str__()
