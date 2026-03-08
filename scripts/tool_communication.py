#!/usr/bin/env python3
# Copyright (c) 2021 PickNik, Inc.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the {copyright_holder} nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


"""Small helper script to start the tool communication interface."""

import subprocess
import logging
import argparse

def get_args():
    arg = argparse.ArgumentParser(description="Starts socat to create a PTY symlink for the UR tool communication interface.")
    arg.add_argument("--robot-ip", default="192.168.56.101", help="Robot IP.")
    arg.add_argument("--tcp-port", type=int, default=54321, help="TCP Port.")
    arg.add_argument("--device-name", default="/tmp/ttyUR", help="PTY symlink device name.")
    return arg.parse_args()

def main():

    args = get_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    # Get parameters from arguments
    robot_ip = args.robot_ip
    logging.info("Robot IP: " + robot_ip)
    tcp_port = args.tcp_port
    logging.info("TCP Port: " + str(tcp_port))
    local_device = args.device_name

    cfg_params = ["pty"]
    cfg_params.append("link=" + local_device)
    cfg_params.append("raw")
    cfg_params.append("ignoreeof")
    cfg_params.append("waitslave")

    cmd = ["socat"]
    cmd.append(",".join(cfg_params))
    cmd.append(":".join(["tcp", robot_ip, str(tcp_port)]))

    logging.info(f"Configuring PTY symlink at '{local_device}'")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    except FileNotFoundError:
        logging.fatal("Socat not found in PATH. Install it (e.g. apt-get install socat).")
        return
    
    except subprocess.TimeoutExpired:
        logging.error("Timeout while starting socat. Check network reachability and port openness.")
        return
    
    except Exception as e:
        logging.fatal(f"Unexpected error launching socat: {e}")
        return

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        logging.error(f"Socat returned non-zero exit code: {result.returncode}")
        if stderr:
            logging.error(f"Socat stderr output: {stderr}")

            if "Is a directory" in stderr and "unlink(" in stderr:
                logging.error(
                    "It looks like the 'link=' path refers to a directory. "
                    "Choose a different file path for link= (e.g., '/tmp/ttyUR0' or '/tmp/ttyUR/port'). "
                    "Ensure the parent directory exists, but the link target itself does not exist as a directory."
                )

        else:
            logging.error("No additional error information available from socat.")

        return
    
    logging.info("Socat started successfully.")
    logging.info("Remote device is available at '" + local_device + "'")

    return

if __name__ == "__main__":
    main()