//
// Created by Keren Dong on 2020/5/22.
//

#include <kungfu/yijinjing/journal/assemble.h>
#include <kungfu/yijinjing/time.h>

namespace kungfu::yijinjing::journal {
struct noop_publisher : public publisher {
  noop_publisher() = default;
  bool is_usable() override { return true; }
  void setup() override {}
  int notify() override { return 0; }
  int publish(const std::string &json_message) override { return 0; }
};

struct assemble_exception : std::runtime_error {
  explicit assemble_exception(const std::string &msg) : std::runtime_error(msg){};
};

sink::sink() : publisher_(std::make_shared<noop_publisher>()) {}

publisher_ptr sink::get_publisher() { return publisher_; }

fixed_sink::fixed_sink(data::locator_ptr locator) : sink(), locator_(std::move(locator)) {}

writer_ptr fixed_sink::get_writer(const data::location_ptr &location, uint32_t dest_id, const frame_ptr &frame) {
  if (writers_.find(dest_id) == writers_.end()) {
    auto target_location = data::location::make_shared(*location, locator_);
    writers_.try_emplace(dest_id, std::make_shared<writer>(target_location, dest_id, true, get_publisher()));
  }
  return writers_.at(dest_id);
}

assemble::assemble(const std::vector<data::locator_ptr> &locators, const std::string &mode, const std::string &category,
                   const std::string &group, const std::string &name)
    : publisher_(std::make_shared<noop_publisher>()), mode_(mode), category_(category), group_(group), name_(name) {
  for (auto &locator : locators) {
    locators_.push_back(locator);
    readers_.push_back(std::make_shared<reader>(true));
    auto reader = readers_.back();
    for (auto &location : locator->list_locations(category, group, name, mode)) {
      for (auto dest_id : locator->list_location_dest(location)) {
        reader->join(location, dest_id, 0);
      }
    }
  }
  sort();
}

assemble assemble::operator+(assemble &other) {
  if (mode_ != other.mode_ or category_ != other.category_ or group_ != other.group_ or name_ != other.name_) {
    auto msg = fmt::format("assemble incompatible: {}/{}/{}/{}, {}/{}/{}/{}", category_, group_, name_, mode_,
                           other.category_, other.group_, other.name_, other.mode_);
    throw assemble_exception(msg);
  }
  std::vector<data::locator_ptr> merged_locators = {};
  merged_locators.insert(merged_locators.end(), locators_.begin(), locators_.end());
  merged_locators.insert(merged_locators.end(), other.locators_.begin(), other.locators_.end());
  return assemble(merged_locators, mode_, category_, group_, name_);
}

void assemble::operator>>(const sink_ptr &sink) {
  if (used_) {
    throw assemble_exception("assemble has already been used");
  }
  used_ = true;
  std::unordered_map<uint32_t, std::unordered_map<uint32_t, writer_ptr>> writer_maps = {};
  while (data_available()) {
    auto page = current_reader_->current_page();
    auto location = page->get_location();
    auto dest_id = page->get_dest_id();
    auto frame = current_reader_->current_frame();
    auto writer = sink->get_writer(location, dest_id, frame);
    writer->copy_frame(frame);
    next();
  }
}

bool assemble::data_available() {
  for (auto &reader : readers_) {
    if (reader->data_available()) {
      return true;
    }
  }
  return false;
}

void assemble::next() {
  if (current_reader_ and current_reader_->data_available()) {
    current_reader_->next();
  }
  sort();
}

void assemble::sort() {
  int64_t min_time = INT64_MAX;
  for (auto &reader : readers_) {
    if (reader->data_available() and reader->current_frame()->gen_time() < min_time) {
      min_time = reader->current_frame()->gen_time();
      current_reader_ = reader;
    }
  }
}
} // namespace kungfu::yijinjing::journal