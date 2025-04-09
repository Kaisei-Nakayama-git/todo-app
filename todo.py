# todo.py

todos = []

def add_task(title):
    todos.append({"title": title, "done": False})

def list_tasks():
    if not todos:
        print("タスクがありません。")
        return

    print("現在のTodo一覧：")
    for i, task in enumerate(todos):
        status = "✔️ 完了" if task["done"] else "❌ 未完了"
        print(f"{i + 1}. {task['title']} [{status}]")

def mark_done(index):
    if 0 <= index < len(todos):
        todos[index]["done"] = True
        print(f"「{todos[index]['title']}」を完了にしました。")
    else:
        print("その番号のタスクは存在しません。")

def main():
    while True:
        print("\n--- メニュー ---")
        print("1. タスクを追加")
        print("2. タスクを表示")
        print("3. タスクを完了にする")
        print("4. 終了")
        choice = input("番号を選んでください: ")

        if choice == "1":
            title = input("タスクの名前を入力してください: ")
            add_task(title)
        elif choice == "2":
            list_tasks()
        elif choice == "3":
            list_tasks()
            try:
                index = int(input("完了にするタスクの番号: ")) - 1
                mark_done(index)
            except ValueError:
                print("番号を正しく入力してください。")
        elif choice == "4":
            print("終了します。")
            break
        else:
            print("1〜4の番号を入力してください。")

if __name__ == "__main__":
    main()
