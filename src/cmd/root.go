package cmd

import (
	"os"
	"github.com/spf13/cobra"
)



var rootCmd = &cobra.Command{
	Use:   "dfctl",
	Short: "A dotfiles manager",
	Long: `Used to manage your dotfiler from a github repo`,
}

func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

// Root Flags 
var (
    NoConfirm 	bool
    AutoPull 	bool
    AutoPush 	bool
)
func init() {
    rootCmd.Flags().BoolVar(&NoConfirm, "noconfirm", false, "Remove confirmations")
    rootCmd.Flags().BoolVar(&AutoPull, "autopull", true, "Auto pull before any action")
    rootCmd.Flags().BoolVar(&AutoPush, "autopush", true, "Auto push after any action")
}
