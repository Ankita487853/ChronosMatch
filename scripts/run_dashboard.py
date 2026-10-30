
import time
import random
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.text import Text

console = Console()

total_orders = 0
buy_orders = 0
sell_orders = 0
start_time = time.time()

def create_dashboard():
    global total_orders, buy_orders, sell_orders

    elapsed = time.time() - start_time
    throughput = total_orders / elapsed if elapsed > 0 else 0

    # Demo values until connected to the real matching engine
    avg_latency = random.uniform(20, 45)
    p99_latency = random.uniform(40, 65)

    header = Panel(
        "[bold cyan]CHRONOSMATCH[/bold cyan]\n"
        "[white]ZERO-COPY HIGH-FREQUENCY TRADING ENGINE[/white]",
        border_style="cyan"
    )

    metrics = Table(title="LIVE ENGINE METRICS", expand=True)
    metrics.add_column("Metric", style="cyan")
    metrics.add_column("Value", justify="right", style="green")

    metrics.add_row("Total Orders", f"{total_orders:,}")
    metrics.add_row("Buy Orders", f"{buy_orders:,}")
    metrics.add_row("Sell Orders", f"{sell_orders:,}")
    metrics.add_row("Throughput", f"{throughput:,.0f} orders/sec")
    metrics.add_row("Average Latency", f"{avg_latency:.2f} us")
    metrics.add_row("P99 Latency", f"{p99_latency:.2f} us")

    order_book = Table(title="ORDER BOOK", expand=True)
    order_book.add_column("Side")
    order_book.add_column("Orders", justify="right")

    order_book.add_row("[green]BUY[/green]", str(buy_orders))
    order_book.add_row("[red]SELL[/red]", str(sell_orders))

    layout = Layout()
    layout.split_column(
        Layout(header, size=5),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(metrics),
        Layout(Panel(order_book, border_style="blue"))
    )

    return layout

console.print("[bold green]Starting ChronosMatch Dashboard...[/bold green]")

try:
    with Live(create_dashboard(), refresh_per_second=4, console=console) as live:
        while True:
            total_orders += random.randint(5, 20)

            if random.choice([True, False]):
                buy_orders += 1
            else:
                sell_orders += 1

            live.update(create_dashboard())
            time.sleep(0.25)

except KeyboardInterrupt:
    console.print("\n[bold yellow]Dashboard stopped.[/bold yellow]")
