import socketserver
import threading
import sys

class ChatServer:
    names = set()
    writers = set()
    lock = threading.Lock()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ChatHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            # Ask for a name repreatedly until the client is assigned a valid name
            while True:
                self.wfile.write('SUBMITNAME\n'.encode('utf-8'))
                name = self.rfile.readline().decode('utf-8').strip()

                if name is None:
                    return

                with ChatServer.lock:
                    if name and name not in ChatServer.names:
                        ChatServer.names.add(name)
                        break

            # Now that a successful name has been chosen, add the socket's print writer
            # to the set of all writers so this client can receive broadcast messages.
            # But BEFORE THAT, let everyone else know that the new person has joined!
            self.wfile.write(('NAMEACCEPTED ' + name + '\n').encode('utf-8'))
            for writer in ChatServer.writers:
                writer.write(
                    ("MESSAGE " + name + " has joined\n").encode('utf-8'))
            ChatServer.writers.add(self.wfile)

            # Accepts messages from this client and broadcasts them
            while True:
                input = self.rfile.readline().decode('utf-8').strip()

                if input.lower().startswith('\quit'):  # pylint: disable=anomalous-backslash-in-string
                    return

                for writer in ChatServer.writers:
                    writer.write(("MESSAGE " + name + ": " + input + '\n').encode('utf-8'))

        except:  # catch *all* exceptions
            print(sys.exc_info()[0])

        finally:
            if self.wfile is not None:
                ChatServer.writers.remove(self.wfile)

            if name is not None:
                print(name + " is leaving")
                ChatServer.names.remove(name)
                for writer in ChatServer.writers:
                    writer.write(("MESSAGE " + name + " has left\n").encode('utf-8'))
            

with ThreadedTCPServer(('', 59001), ChatHandler) as server:
    print(f'The chat server is running...')
    server.serve_forever()
