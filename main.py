from direct.showbase.ShowBase import ShowBase

class BreachShift(ShowBase):
    def __init__(self):
        super().__init__()

        self.setBackgroundColor(0.05, 0.05, 0.08)
        self.accept("escape", self.userExit)
        
if __name__ == "__main__":
    game = BreachShift()
    game.run()