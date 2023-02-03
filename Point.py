class Point:
    def __init__(self, x: float, y: float):
        self._x = x
        self._y = y

    
    def __get__(self) -> tuple[float, float]:
        return (self._x, self._y)


    def translate(self, dx: float = 0.0, dy: float = 0.0):
        self._x += dx
        self._y += dy

    
    @property
    def x(self):
        return self._x
    

    @property
    def y(self):
        return self._y