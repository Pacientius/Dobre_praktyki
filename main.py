
from consumer import start_consumer 
from producer import add_tasks_bulk  


def produce_100_tasks():
    print("[MAIN] Generuję 100 zadań.")  
    add_tasks_bulk(100)  
    print("[MAIN] Dodano 100 zadań") 


if __name__ == "__main__":

    produce_100_tasks()


    print("[MAIN] Uruchamiam consumerów...")
    start_consumer() 
