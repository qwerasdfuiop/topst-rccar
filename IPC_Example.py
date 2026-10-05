import argparse
import threading
from Library.IPC_Library import IPC_SendPacketWithIPCHeader, IPC_ReceivePacketFromIPCHeader
from Library.IPC_Library import TCC_IPC_CMD_CA72_EDUCATION_CAN_DEMO, IPC_IPC_CMD_CA72_EDUCATION_CAN_DEMO_START
from Library.IPC_Library import parse_hex_data, parse_string_data, parse_channels, parse_hex16
sndfile = open("/dev/tcc_ipc_micom",'wb')

# VCP CAN IDs (must match sources/app.sample/app.base/vcp_types.h)
VCP_IO_EMER_BRAKE = 0x108
VCP_IO_ACTION_ON = 0x01

def sendtoCAN(channel, canId, sndDataHex):
        sndData = parse_hex_data(sndDataHex)
        uiLength = len(sndData)
        ret = IPC_SendPacketWithIPCHeader(sndfile, channel_bitmask, tx_only_channel_bitmask, canID, sndData)

def receiveFromCAN():
        micom_thread = threading.Thread(target=IPC_ReceivePacketFromIPCHeader, args=("/dev/tcc_ipc_micom", 1))
        micom_thread.start()

def send_can_packet(file_path, channel_bitmask, tx_only_channel_bitmask, canID, sndData):
    if channel_bitmask == 0 or channel_bitmask & ~0x7:
        print("Error: channel bitmask must be a non-zero value using only bits 0~2 (max value: 0x7).")
        return False

    if tx_only_channel_bitmask & ~0x7:
        print("Error: txOnly bitmask should only use bits 0~3 (max value 0x7).")
        return False

    sndDataLength = len(sndData)
    channel_str = ", ".join(parse_channels(channel_bitmask))
    txonly_str = ", ".join(parse_channels(tx_only_channel_bitmask))
    print(f"channel_bitmask: 0x{channel_bitmask:02X} (channels: {channel_str or 'None'})")
    print(f"tx_only_channel_bitmask: 0x{tx_only_channel_bitmask:02X} (channels: {txonly_str or 'None'})")
    print(f"canID: 0x{canID:04X}")
    print(f"sndData: {sndData}")
    print(f"sndDataLength: {sndDataLength}")

    IPC_SendPacketWithIPCHeader(file_path, channel_bitmask, tx_only_channel_bitmask, canID, sndData)
    return True

def main():
    parser = argparse.ArgumentParser(description="IPC Sender/Receiver")
    parser.add_argument("mode", choices=["snd", "rev", "sndrecv", "emer_brake"],
                        help="'snd': send, 'rev': receive, 'sndrecv': send then receive once, "
                             "'emer_brake': emergency brake (suspend MotorSpeedTask, IN1-IN4 LOW)")
    parser.add_argument("--file_path", default=sndfile, help="File path for IPC communication")
    parser.add_argument("--channel", type=int, default=1, help="can channel bit flag: b111")
    parser.add_argument("--txOnly", type=int, default=0, help="tx only channel bit flag: b111 (dec: 1, 2, 4) ")
    parser.add_argument("--canID", type=parse_hex16, default=0, help="CAN ID max 16-bit: e.g. 123 or 0x1234")
    parser.add_argument("--sndDataHex", type=str, help="Value for sndData as a hex string, e.g., '12345678' (default: string)")
    parser.add_argument("--sndData", type=str, default="12345678", help="Default data if no sndDataHex provided")

    args = parser.parse_args()
    print(f"args.mode: {args.mode}, args.channel: {args.channel}, args.txOnly: {args.txOnly}, args.canID: 0x{args.canID:04X}")

    # Handle 'snd' or 'sndrecv'
    if args.mode in ["snd", "sndrecv"]:
        if args.sndDataHex:
            sndData = parse_hex_data(args.sndDataHex)
        elif args.sndData and len(args.sndData) > 0:
            sndData = parse_string_data(args.sndData)
        else:
            print("Error: No data provided")
            return

        send_can_packet(args.file_path, args.channel, args.txOnly, args.canID, sndData)

    elif args.mode == "emer_brake":
        print("Emergency brake: CAN ID 0x108, data 0x01")
        send_can_packet(args.file_path, args.channel, args.txOnly,
                        VCP_IO_EMER_BRAKE, parse_hex_data("01"))

    # Handle 'rev' or 'sndrecv'
    if args.mode == "rev":
        threading.Thread(target=IPC_ReceivePacketFromIPCHeader,
            args=(args.file_path,),
            kwargs={"recv_count": None, "recv_timeout": None},
            daemon=True
        ).start()
        threading.Event().wait()  # Wait forever

        #ca53_thread = threading.Thread(target=IPC_ReceivePacketFromIPCHeader, args=("/dev/tcc_ipc_ap", 1))
        #ca53_thread.start()
    elif args.mode == "sndrecv":
        print("Receiving one response with timeout...")
        IPC_ReceivePacketFromIPCHeader(args.file_path, recv_count=1, recv_timeout=3.0)

if __name__ == "__main__":
    main()

#python3 IPC_Example.py rev
#python3 IPC_Example.py snd
#python3 IPC_Example.py sndrecv --canID 1 --sndData 12345
#python3 IPC_Example.py emer_brake
#python3 IPC_Example.py snd --canID 0x108 --sndDataHex 01
