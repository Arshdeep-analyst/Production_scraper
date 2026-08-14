import random
import time 


class HumanBehaviour:

    @staticmethod
    def warm_up(page):
        print("🟢 Warming up browser...")

        page.wait_for_timeout(random.randint(2000, 4000))

        HumanBehaviour.move_mouse(page)

        HumanBehaviour.scroll(page)

        page.wait_for_timeout(random.randint(1000, 3000))


    @staticmethod
    def move_mouse(page):
        width = page.viewport_size["width"]
        height = page.viewport_size["height"]

        moves = random.randint(5, 10)


        for _ in range(moves):

            x = random.randint(50, width - 50)
            y = random.randint(50, height - 50)

            page.mouse.move(
                x,
                y,
                steps=random.randint(15,35)
            )

            page.wait_for_timeout(random.randint(200, 600))

    @staticmethod
    def scroll(page):

        scrolls = random.randit(2, 4)

        for _ in range(scrolls):

            page.mouse.wheel(
                0,
                random.randint(300, 900)
            )

            page.wait_for_timeout(random.randint(500, 1200))

        if random.randint() > 0.5:

            page.mouse.wheel(
                0,
                -random.randint(200, 600)
            )

            page.wait_for_timeout(random.randint(500, 1000))


    @staticmethod
    def short_break():

        seconds = random.uniform(2, 5)

        print(f"😴 Short Break ({seconds:.1f}s)")
        time.sleep(seconds)

    @staticmethod
    def long_break():

        seconds = random.uniform(20, 40)

        print(f"😴 Long Break({seconds:.1f}s)")
        time.sleep(seconds)     