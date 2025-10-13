def print_help():
	print("""
Users: alice, bob, cecil, dave

Commands:
  add-transaction <sender> <receiver> <amount> 			   Add a new transaction
  show-pending                                             Show pending transactions
  mine-block                                               Mine a new block
  show-chain                                               Show the blockchain
  show-block <index>                                       Show a specific block
  validate                                                 Validate the blockchain
  help                                                     Show this help message
  exit                                                     Exit the CLI

  run-file <filename>                                      For faster simulation purposes
	""")


def cli(blockchain):
	print("Welcome to the Blockchain CLI!")
	print("=" * 50)
	print_help()
	while True:
		cmd = input("blockchain> ").strip()
		if not cmd:
			continue
		args = cmd.split()
		if args[0] == 'add-transaction' and len(args) == 4:
			sender, receiver, amount = args[1:]
			blockchain.add_transaction(sender, receiver, amount)
			print("Transaction added.")
			print("=" * 50)
		elif args[0] == 'show-pending':
			print("Pending Transactions:")
			print("=" * 50)
			blockchain.show_pending()
			print("=" * 50)
		elif args[0] == 'mine-block':
			blockchain.mine_block()
			print("=" * 50)
		elif args[0] == 'show-chain':
			print("Blockchain:")
			print("=" * 50)
			blockchain.show_chain()
			print("=" * 50)
		elif args[0] == 'show-block' and len(args) == 2:
			index = int(args[1])
			print(f"Block {index} Details:")
			print("=" * 50)
			blockchain.show_block(index)
			print("=" * 50)
		elif args[0] == 'validate':
			blockchain.validate_chain()
			print("=" * 50)
		elif args[0] == 'run-file' and len(args) == 2:
			run_file(blockchain, args[1])
			print("=" * 50)
		elif args[0] == 'help':
			print_help()
			print("=" * 50)
		elif args[0] == 'exit':
			print("Exiting CLI.")
			break
		else:
			print("Unknown command. Type 'help' for a list of commands.")
			print("=" * 50)

def run_file(blockchain, filename):
	try:
		with open(filename, 'r') as f:
			commands = f.readlines()
	except FileNotFoundError:
		print(f"File '{filename}' not found.")
		return

	for line in commands:
		cmd = line.strip()
		if not cmd or cmd.startswith('#'):
			continue
		print(f"Executing: {cmd}")
		args = cmd.split()
		if args[0] == 'add-transaction' and len(args) == 4:
			sender, receiver, amount = args[1:]
			blockchain.add_transaction(sender, receiver, amount)
			print("Transaction added.")
		elif args[0] == 'show-pending':
			blockchain.show_pending()
		elif args[0] == 'mine-block':
			blockchain.mine_block()
		elif args[0] == 'show-chain':
			blockchain.show_chain()
		elif args[0] == 'show-block' and len(args) == 2:
			blockchain.show_block(int(args[1]))
		elif args[0] == 'validate':
			blockchain.validate_chain()
		elif args[0] == 'help':
			print_help()
		else:
			print(f"Unknown command in file: {cmd}\n")
