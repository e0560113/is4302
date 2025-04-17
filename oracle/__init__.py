from dotenv import load_dotenv
from oracle.oracle import Oracle
import os

def run():
    load_dotenv()
    oracle = Oracle()


if __name__ == "__main__":
    run()
