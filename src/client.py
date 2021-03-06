import asyncio
import sys
from rpcudp.protocol import RPCProtocol

from helper import read_config_file


class RPCServer(RPCProtocol):
    def __init__(self):
        super().__init__()
        self._waitTimeout = 60

    # Any methods starting with "rpc_" are available to clients.
    def rpc_print_result(self, sender, result_line, is_error):
        try:
            new_result = result_line.strip().decode()
        except AttributeError:
            new_result = result_line
        if is_error:
            print(new_result, file=sys.stderr)
        else:
            print(new_result)
        return "result printed"

    def rpc_end_connection(self, sender):
        loop = asyncio.get_event_loop()
        loop.stop()
        print("\n---------Connection ended-------------")
        return "connection ended"


class Client:
    def __init__(self, client_address, server_address):
        print("----- Starting UDP-RPC client -----")
        self.server_address = server_address
        self.client_address = client_address
        # Start local UDP server to be able to handle responses
        loop = asyncio.get_event_loop()
        connect = loop.create_datagram_endpoint(
            RPCServer, local_addr=client_address)
        transport, protocol = loop.run_until_complete(connect)
        self.protocol = protocol
        self.transport = transport

    @asyncio.coroutine
    def run_command(self, command):
        result = yield from self.protocol.run_command(self.server_address, command)
        print("'%s': %s\n" % (command, result[1]) if result[0] else "No response received.")


def main():
    # read arguments
    if len(sys.argv) < 4:
        print("Arguments should be: CLIENT_ADDRESS CLIENT_PORT COMMAND!")
        exit(-1)
    client_ip = sys.argv[1]
    client_port = sys.argv[2]
    remote_command = sys.argv[3]

    server_config = read_config_file('config.ini')

    client = Client((client_ip, int(client_port)), (server_config['ip'], int(server_config['port'])))

    # call remote command
    loop = asyncio.get_event_loop()
    func = client.run_command(remote_command)
    loop.run_until_complete(func)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    client.transport.close()
    loop.close()


if __name__ == "__main__":
    main()
