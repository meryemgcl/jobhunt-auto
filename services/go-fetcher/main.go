package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync"
	"time"
)

type FetchRequest struct {
	Source string `json:"source"`
	URL    string `json:"url"`
}

type FetchResult struct {
	Source     string      `json:"source"`
	URL        string      `json:"url"`
	Data       interface{} `json:"data,omitempty"`
	Error      string      `json:"error,omitempty"`
	StatusCode int         `json:"status_code"`
	DurationMs int64       `json:"duration_ms"`
}

func main() {
	if len(os.Args) < 2 {
		log.Fatalf("Kullanim: %s <requests.json>", os.Args[0])
	}
	file, err := os.Open(os.Args[1])
	if err != nil {
		log.Fatalf("Dosya okunamadi: %v", err)
	}
	defer file.Close()

	var requests []FetchRequest
	if err := json.NewDecoder(file).Decode(&requests); err != nil {
		log.Fatalf("JSON parse hatasi: %v", err)
	}

	results := fetchConcurrent(requests)

	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		log.Fatalf("Cikti JSON yapilamadi: %v", err)
	}
	fmt.Println(string(output))
}

func fetchConcurrent(requests []FetchRequest) []FetchResult {
	var wg sync.WaitGroup
	resultChan := make(chan FetchResult, len(requests))

	client := &http.Client{
		Timeout: 15 * time.Second,
	}

	for _, req := range requests {
		wg.Add(1)
		go func(r FetchRequest) {
			defer wg.Done()
			
			start := time.Now()
			res := FetchResult{Source: r.Source, URL: r.URL}
			
			// HTTP Request
			httpReq, err := http.NewRequest("GET", r.URL, nil)
			if err != nil {
				res.Error = err.Error()
				resultChan <- res
				return
			}
			httpReq.Header.Set("User-Agent", "JobHunt-Auto/1.0 (Polyglot Fetcher)")

			resp, err := client.Do(httpReq)
			res.DurationMs = time.Since(start).Milliseconds()
			
			if err != nil {
				res.Error = err.Error()
				resultChan <- res
				return
			}
			defer resp.Body.Close()
			
			res.StatusCode = resp.StatusCode

			bodyBytes, err := io.ReadAll(resp.Body)
			if err != nil {
				res.Error = err.Error()
				resultChan <- res
				return
			}

			// Try parsing as JSON if possible
			var jsonData interface{}
			if err := json.Unmarshal(bodyBytes, &jsonData); err == nil {
				res.Data = jsonData
			} else {
				// Fallback to string if it's not JSON (e.g. HTML)
				res.Data = string(bodyBytes)
			}
			
			resultChan <- res
		}(req)
	}

	wg.Wait()
	close(resultChan)

	var final []FetchResult
	for res := range resultChan {
		final = append(final, res)
	}
	return final
}
