# Standard library imports
import argparse

# Local imports
from .arm import ARMHarvester
from .ieda import IEDAHarvester


def setup_parser(id):

    description = f"Harvest metadata from {id.upper()}."
    epilog = (
        "Not supplying an argument to both the certificate and key arguments "
        "will disable client side authentication."
    )
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    help = f"Verbosity level of log file {id}.log"
    choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    parser.add_argument('-v', '--verbose', choices=choices, default='INFO',
                        help=help)

    help = (
        "Harvest records to this dataone node host.  This is NOT "
        "the host where the site map is found."
    )
    parser.add_argument('--host', default='localhost', help=help)

    help = "DataONE host SSL port."
    parser.add_argument('--port', default=443, type=int, help=help)

    help = 'Path to dataone host certificate.'
    parser.add_argument('--certificate', default=None, help=help)

    help = 'Path to dataone host private key.'
    parser.add_argument('--key', default=None, help=help)

    return parser


def arm():
    parser = setup_parser("arm")
    args = parser.parse_args()

    arm_harvester = ARMHarvester(args.host, port=args.port,
                                 verbosity=args.verbose,
                                 certificate=args.certificate,
                                 private_key=args.key)
    arm_harvester.run()


def ieda():
    parser = setup_parser("ieda")
    args = parser.parse_args()

    ieda_harvester = IEDAHarvester(args.host, port=args.port,
                                   verbosity=args.verbose,
                                   certificate=args.certificate,
                                   private_key=args.key)
    ieda_harvester.run()
