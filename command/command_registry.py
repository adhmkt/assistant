# command/command_registry.py

from .command import *  # Import all commands from command.py

class CommandRegistry:
    def __init__(self):
        self.commands = {
            'generate_image': GenerateImageCommand(),
            'get_used_car_prices': GetUsedCarPricesCommand(), 
            'authenticate_and_log': AuthenticateAndLogCommand(), 
            # Add other commands to this dictionary
        }

    async def execute_command(self, command_name, arguments):
        command = self.commands.get(command_name)
        if command is None:
            raise ValueError(f"No command found for {command_name}")
        return await command.execute(arguments)
