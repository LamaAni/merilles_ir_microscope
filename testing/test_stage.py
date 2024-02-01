# %% Configure NI device
from nidaqmx import Task

task = Task(new_task_name="TestTask")

# %%  Configure the task


def add_ao_voltage_chan(task: Task, name: str, channel: str):
    task.ao_channels.add_ao_voltage_chan(
        physical_channel=channel,
        name_to_assign_to_channel=name,
        max_val=5,
        min_val=0,
    )


add_ao_voltage_chan(task, "X", "/Dev1/ao0")
add_ao_voltage_chan(task, "Y", "/Dev1/ao1")


# %% Set poisitional voltage


def set_position(x, y):
    if not task.is_task_done():
        task.stop()
    task.start()
    task.write([[x], [y]], auto_start=False)
    task.stop()


set_position(0, 0)
