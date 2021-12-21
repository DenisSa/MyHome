from influxdb_client import Point


class SystemStats:
    def __new__(cls, router, cpu, mem, uptime):
        return Point("SystemStats").tag("router", router).field("cpu", int(cpu)).field("mem", int(mem)).field("uptime", int(uptime))


class Interfaces:
    def __new__(cls, router, ifname, rx_packets, rx_bytes, rx_errors, rx_dropped, tx_packets, tx_bytes, tx_errors,
                tx_dropped, rx_bps, tx_bps):
        return Point("Interfaces")\
            .tag("router", router)\
            .tag("ifname", ifname)\
            .field("rx_packets", int(rx_packets))\
            .field("rx_bytes", int(rx_bytes))\
            .field("rx_errors", int(rx_errors))\
            .field("rx_dropped", int(rx_dropped)) \
            .field("rx_bps", int(rx_bps))\
            .field("tx_packets", int(tx_packets))\
            .field("tx_bytes", int(tx_bytes))\
            .field("tx_errors", int(tx_errors))\
            .field("tx_dropped", int(tx_dropped))\
            .field("tx_bps", int(tx_bps))


class LatencyPoint:
    def __new__(cls, router, target, latency, lost):
        return Point("Latency") \
            .tag("router", router) \
            .tag("target", target) \
            .field("latency", float(latency)) \
            .field("lost", int(lost))

# @lineprotocol
# class Clients(NamedTuple):
#     router: TAG
#     num_active: INT


# @lineprotocol
# class DPI(NamedTuple):
#     router: TAG
#     client_id: TAG
#     client_name: TAG
#     dpi: TAG
#     dpi_category: TAG
#     rx_bytes: INT
#     tx_bytes: INT

# @lineprotocol
# class Users(NamedTuple):
#     router: TAG
#     user_type: TAG
#     count: INT
