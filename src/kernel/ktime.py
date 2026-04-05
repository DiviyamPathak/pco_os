from khal import wait_for_interrupt
from kapic import arm_timer_periodic
from kapic import reset_timer_ticks
from kapic import timer_tick_count
from kconsole import console_write_label_u64
from kconsole import console_write_line
from ksupport import panic


def start_kernel_tick_source(initial_count: int):
    reset_timer_ticks()
    arm_timer_periodic(initial_count)


def current_kernel_ticks():
    return timer_tick_count()


def wait_for_tick_edge():
    start = current_kernel_ticks()
    current = start
    while current == start:
        wait_for_interrupt()
        current = current_kernel_ticks()
    return current


def wait_for_kernel_ticks(delta: int):
    if delta <= 0:
        panic("tick wait requires positive delta".c_str())

    start = current_kernel_ticks()
    target = start + delta
    current = start
    while current < target:
        current = wait_for_tick_edge()
    return current


def timekeeping_self_test(delta: int):
    start = current_kernel_ticks()
    end = wait_for_kernel_ticks(delta)

    if end < start + delta:
        panic("timekeeping tick wait failed".c_str())

    console_write_label_u64("time.ticks.start=".c_str(), start)
    console_write_label_u64("time.ticks.end=".c_str(), end)
    console_write_line("timekeeping self-test ok".c_str())
