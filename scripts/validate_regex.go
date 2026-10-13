// Compile every expression with the same Go regexp semantics used by consumers.
package main

import (
	"encoding/json"
	"os"
	"regexp"
)

func main() {
	var expressions []string
	if json.NewDecoder(os.Stdin).Decode(&expressions) != nil {
		os.Exit(1)
	}
	for _, expression := range expressions {
		if _, err := regexp.Compile(expression); err != nil {
			os.Exit(1)
		}
	}
}
