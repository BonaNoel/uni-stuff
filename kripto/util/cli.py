def print_help():
	print("""
Commands:
  add-transaction <sender> <receiver> <amount> <signature>  Add a new transaction
  show-pending                                             Show pending transactions
  mine-block                                               Mine a new block
  show-chain                                               Show the blockchain
  show-block <index>                                       Show a specific block
  validate                                                 Validate the blockchain
  help                                                     Show this help message
  exit                                                     Exit the CLI
	""")

def cli(blockchain):
	print("Welcome to the Blockchain CLI!")
	print_help()
	while True:
		cmd = input("blockchain> ").strip()
		if not cmd:
			continue
		args = cmd.split()
		if args[0] == 'add-transaction' and len(args) == 5:
			sender, receiver, amount, signature = args[1:]
			blockchain.add_transaction(sender, receiver, amount, signature)
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
		elif args[0] == 'exit':
			print("Exiting CLI.")
			break
		else:
			print("Unknown command. Type 'help' for a list of commands.")
